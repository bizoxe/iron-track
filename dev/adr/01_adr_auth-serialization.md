## ADR-01: Authentication & Serialization

**Status:** Accepted

**Date:** 2026-05-26

---

## Context

Based on the results of load testing and profiling in [auth-serialization.md](../../benchmarks/auth-serialization.md), it was established that:
* **Authentication:**
  * Synchronous password hashing (`Argon2id`) at the ORM level (`advanced-alchemy`) leads to blocking of the event loop.
  * Cryptographic signing of access/refresh tokens using the `RSA-2048` algorithm also leads to event loop blocking and takes up a total of ~66% of processor time for the `/signin` endpoint.
* **Access Control:** The `RSA-2048` algorithm was replaced with `Ed25519`. Cryptographic signing of tokens via the `Ed25519` algorithm is "cheaper" compared to the asymmetric `RSA-2048` algorithm, but it introduces significant overhead during signature verification (taking ~20-22% of processor time versus ~10-12% for the `RSA-2048` algorithm).
* **Serialization:** The project implements `MsgSpecJSONResponse`, but for versatility and compatibility with Pydantic models, it is necessary to use `jsonable_encoder` as an intermediate step before serialization - this leads to critical performance degradation and makes it impossible to use the `msgspec` library natively (`msgspec.json`).


### 1. Offload CPU-intensive cryptographic tasks to a ThreadPoolExecutor
**Decision:**
To prevent blocking of the main Event Loop thread, move the password hashing and verification operations (`Argon2id`) to a dedicated `ThreadPoolExecutor` (`crypto_executor`).

* **Implementation:** A mechanism for automatically determining the number of threads based on available processor cores (`os.sched_getaffinity` or `os.cpu_count`) was implemented, with an upper limit of 4 threads to prevent excessive context switching.
* **Usage:** The `hasher.hash` and `hasher.verify_and_update` calls are wrapped in `run_in_executor`, which moves the execution of heavy mathematical operations from the Event Loop to a thread.

**Consequences:**

* **Positive:** Blocking of the Event Loop during heavy cryptographic computations is eliminated. The application workers remain responsive to handle light/medium requests, which is critical to prevent system degradation during user influx.


* **Trade-offs:**
  * **Infrastructure Complexity:** The appearance of a dedicated thread pool requires control over its life cycle.
  * **Memory Overhead:** Each thread in the pool consumes additional system resources (thread stack), although for 4 threads this is negligible.
  * **Context Switching:** Overhead for transferring a task from the Event Loop to a thread via `run_in_executor`, which, however, is completely offset by the benefit of not blocking the main loop.


### 2. Algorithm Migration: RSA-2048 to Ed25519
**Decision:**
Migrate JWT signing from `RSA-2048` (the `PyJWT` library) to `Ed25519` (the `joserfc` library).

* **Rationale:**
  * **Performance:** `Ed25519` demonstrates significantly higher signature generation speed with a comparable level of security.
  * **DX & Infrastructure:** `joserfc` provides native support for `Ed25519` and simplifies key management (generation with a single command, no need to store and version `.pem` files), which optimizes CI/CD pipelines.



**Consequences:**

* **Positive:** Event Loop blocking on the `/signin` endpoint is eliminated, as the asymmetric signature has become computationally "cheaper".


* **Trade-offs:**
  * **Verification Overhead:** Despite the faster signing, `Ed25519` verification in `joserfc` creates an increased CPU load when checking tokens on each request.
  * **Mitigation:** This overhead is compensated by the introduction of caching for access tokens, which minimizes the frequency of cryptographic checks for protected endpoints.


### 3. Access Control: JTI Caching & `cashews` Framework Migration

**Decision:**
Implement JTI caching for access tokens. Migrate from `fastapi-cache2` to `cashews`.

* **Rationale (Migration to `cashews`):**
  * **Decoupling:** Unlike `fastapi-cache2`, which is deeply integrated with the FastAPI DI container, `cashews` provides a clean interface for working with the cache, independent of the web framework. This allows the use of caching mechanisms in the service layers without "passing through" HTTP dependencies.
  * **Advanced Patterns:** `cashews` provides built-in strategies for dealing with cache stampede, rate limiting, etc., which are not available in standard plugins.
  * **DX & Maintenance:** Active development of the library and better support for asynchronous backends.



**Consequences:**

* **Positive:** A **multiplicative effect** was achieved: the authentication mechanism is used in all protected endpoints (`get_current_user`), and local caching of access tokens led to an increase in the throughput of the entire system.


**Trade-offs:**
* **High Refactoring Cost:** The migration required a redesign of the authentication/authorization business logic and adaptation of the test suite.


### 4. Serialization: Transition to `msgspec.json`

**Decision:**
Switch to native serialization via `msgspec.json` on the API output layer.

* **Implementation:**
  * The use of Pydantic models is left for validating incoming data (on input).
  * The use of `msgspec.Struct` is implemented exclusively for serializing outgoing responses.


* **Rationale:**
  * **Performance:** Abandoning `jsonable_encoder` and Pydantic serialization eliminates the main delays in forming JSON responses.
  * **Type-Safety:** Using `msgspec.Struct` ensures strict data typing at the serialization level.


**Consequences:**

* **Positive:** Maximum performance of the output layer is achieved due to the direct mapping of structures to JSON.


* **Trade-offs:**
  * **Increased Complexity:** The need to maintain two data schemas (Pydantic and `msgspec.Struct`) for one entity.
  * **Mitigation:** Separation of responsibilities (validation on input vs. serialization on output) minimizes the risks of desynchronization with strict adherence to the project structure.
