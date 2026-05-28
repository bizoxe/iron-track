## Load Testing Report: Authentication & Serialization

**Test Date:** 2026-05-26

**Status:** Decided

**Target Modules:** [API Endpoints](../src/app/domain/users/controllers/access.py) | [MsgSpecJSONResponse](../src/app/lib/json_response.py)

**Environment:** [Test Bench Specification](SPEC.md)

**Configuration:**
* **Server:** Uvicorn 0.40.0
  * **Flags:** `--loop=uvloop` `--http=httptools` `--backlog=2048`
* **OS Tuning:** `ulimit -n 65535`, `somaxconn=2048`, `overcommit_memory=1`

> **Quick Jump:** [Bottleneck Analysis (1-4)](#bottleneck-analysis) | [Intermediate Tests (1-3)](#bottleneck-analysis-tests-points-1-to-3-inclusive) | [Intermediate Results (1-3)](#tables-with-baseline-and-first-optimization-results) | [Serialization Test (4)](#bottleneck-analysis-test-point-4) | [Final Opt. Tests (1-3)](#bottleneck-analysis-tests-points-1-to-3-inclusive-final-optimization) | [Final Results (1-3)](#the-tables-below-include-the-results-of-the-baseline-first-and-final-optimization-tests) | [Logging Impact](#additional-point-the-impact-of-structured-logging-on-latency) | [DBMS Config](#additional-point-analysis-of-dbms-configuration-io-bound)

#### Abstract
> The purpose of this load testing is to profile and identify bottlenecks (Bottleneck Analysis), followed by optimization and evaluation of the impact of architectural decisions within an educational project. The analysis is aimed at quantifying overhead and is not intended for a production environment.

#### Note: Justification for the relevance of wrk2 metrics (System Jitter)
> A series of 3 tests with 3 runs per series in TTY mode for the `GET /ping` endpoint (returns `b"OK"`) with application/load generator core affinity (0,1/6,7) and disabled uvicorn logs (`/dev/null`) revealed identical peak latencies (Max Latency ~80ms). Also, during three independent test series (sar, TTY mode, uvicorn logs -> `/dev/null`), the repeatability of system anomalies was confirmed: short-term spikes in the task queue (`runq-sz` from 3 to 4) and bursts of context switches (`cswch/s` ~11k), despite the application being allocated only 2 physical cores with sufficient core resources (~75% `idle`); values >2 mathematically confirm a state of preemption. This links the high values of Max Latency, P99, and StdDeviation to the operation of the Linux OS scheduler and hardware interrupt handling, rather than the efficiency of the application code ([sar-logs](https://github.com/bizoxe/iron-track/blob/benchmarks/benchmarks/results/auth-serialization/test-ping/sar-metrics/without-logging/reports/system.txt)).

*The test results will include Max Latency, P99, and StdDeviation values. However, when analyzing the results, we will primarily focus on **Mean Latency** and **P90** for the following reasons:*
* ***On lightweight endpoints**, system jitter manifests in a classic way: Max Latency and P99 disproportionately spike upwards relative to the smooth P90 plateau, artificially inflating `StdDeviation`.*
* ***On heavy (CPU-bound) endpoints**, the overhead from the OS scheduler is physically smoothed out against the background of the long execution of the business logic itself. In this case, the percentile distribution appears smooth, but `Max Latency` and `StdDeviation` still remain noisy due to hardware error.*

---

## Bottleneck Analysis

### 1. Hypothesis for `/api/v1/access/signup` (Registration)

* **Premise:** Using synchronous password hashing at the ORM level (`advanced-alchemy` | `pwdlib.hashers.argon2.Argon2Hasher`) requires significant CPU computational power, and the subsequent data writing involves disk I/O operations.
* **Hypothesis Formulation:** Due to the cooperative nature of asynchrony in Python, performing heavy synchronous hash calculations (`Argon2id`) in the main thread under load from `wrk2` will completely block the Event Loop and the application server worker for the duration of the mathematical operation. This will stop the processing of incoming network events, causing other clients' requests to queue up at the system socket level. The bottleneck will not be the disk subsystem, but the monopolization of the single Event Loop thread by synchronous code (lack of offloading the task to `run_in_executor`).
* **Objective:** Determine whether async offloading of CPU-bound tasks (delegating computations to a `ThreadPoolExecutor`) is required for user password hashing, or if the current synchronous execution is optimal.

### 2. Hypothesis for `/api/v1/access/signin` (Login)

* **Premise:** User authentication involves synchronous password verification (see `/api/v1/access/signup` above), as well as the generation of two tokens (access/refresh) using `RSA-2048` asymmetric cryptography, which requires significant CPU computational power. Searching for the user in the database (I/O) has low latency due to the use of an index (the `email` column).
* **Hypothesis Formulation:** See point one. On this endpoint, the situation will worsen: the worker will sequentially hang first on password verification, and then be blocked twice by RSA-2048 asymmetric encryption when generating signatures for the access and refresh tokens. The total time a single request monopolizes the thread will increase several times over.
* **Objective:** Verify the hypothesis that the sequential execution of CPU-bound operations (password verification + RSA signatures) is a critical bottleneck, and evaluate the feasibility of switching to signature algorithms with lower computational costs (`Ed25519`).

### 3. Hypothesis for `/api/v1/access/me` (Get User Profile)
* **Premise:** The endpoint relies on the `get_current_active_user` dependency. On each request, the JWT token is first decoded (RSA-2048 asymmetric algorithm via `decode_jwt`). After successful validation, the cache is checked (decorator `@cache` from `fastapi_cache.decorator`). On a cache hit, the bytes are retrieved and deserialized (calling `msgspec.msgpack.decode` + `UserAuth.model_validate`). On a cache miss, a database query is executed, followed by converting the ORM object to `UserAuth` and saving it to the cache (serialized using `msgspec.msgpack.encode` + `jsonable_encoder`).
* **Hypothesis Formulation:** With a cache, we reduce the load on the database but transfer part of the load to the CPU (deserialization). However, as the load on the endpoint increases, the cryptographic decoding and verification of the JWT (RSA-2048) will place a noticeable load on the CPU and reduce overall throughput. Deserialization will not have a significant impact.
* **Objective:** Evaluate the computational costs of decoding and cryptographically verifying access tokens when using the `RSA-2048` algorithm.

**Note:** Authentication/Authorization chain execution flow

```text
[HTTP Request]
     │
     ▼
[Dependency Depends(access_token)]
     │
     ▼
[1. Decode token: get_payload_from_token()]
     │
     ├── ❌ decode_jwt() using PyJWT - CPU-bound (RSA-2048 modular arithmetic)
     └── Structure and exception check
     │
     ▼
[2. Get user: Authenticate.get_current_user()]
     │
     └── Pass token_payload["sub"] to _get_user_from_payload() method
     │
     ▼
[3. Check cache / Get data]
     │
     ├── ✔️ Cache hit: Deserialization (MsgPackCoderUserAuth) — CPU-bound
     │    └─ (msgspec.msgpack.decode + UserAuth.model_validate)
     │
     └── ❌ Cache miss: I/O-bound
          ├── DB query (users_service.get)
          └── Convert to UserAuth schema (users_service.to_schema) and write to cache (msgspec.msgpack.encode + jsonable_encoder)
     │
     ▼
[4. Additional checks (depending on the endpoint)]
     │
     ├── get_current_active_user — check is_active
     └── superuser_required / trainer_required — check is_superuser or role_slug
```

### 4. Hypothesis for `MsgSpecJSONResponse (msgspec.json)` (Serialization)

* **Premise:** The project implements a custom `MsgSpecJSONResponse`, but for versatility and compatibility with Pydantic models, we are forced to use `jsonable_encoder` as an intermediate step before serialization.
* **Hypothesis Formulation:** On high-load endpoints or when serializing large volumes of data, the overhead of `jsonable_encoder` will cause noticeable latency and increase the CPU load. It is expected that the overhead of `jsonable_encoder` will be partially compensated by the `msgspec` library.

**Note 1:** How jsonable_encoder works: `jsonable_encoder` traverses all objects, including lists and nested dictionaries, checks types, and converts complex structures (e.g., datetime, UUID, Pydantic models) into standard Python types. New intermediate objects are created for each such operation. This leads to excessive memory allocation and additional load on the garbage collector.

**Note 2:** Before the release of Pydantic v2, using `jsonable_encoder` + `orjson` did provide a performance boost because, despite the overhead of `jsonable_encoder`, the final byte assembly was faster than the standard mechanisms of the FastAPI framework.

**Objective:**
1. Evaluate the efficiency of serialization via `MsgSpecJSONResponse` compared to the standard "out-of-the-box" serialization of Pydantic models by the FastAPI framework.
2. Determine if it makes sense to introduce separate `msgspec.Struct` "output" schemas into the project just for serialization to achieve maximum performance.

---

## Bottleneck Analysis Tests (Points 1 to 3 inclusive)

**Note 1:** Profiling with py-spy, baseline tests, and tests after the first optimization were carried out with the default `Argon2id` settings.

* **Note 2:** The first optimization included:
  * Changing the **PyJWT** library to **joserfc** and the token signing algorithm from `RSA-2048` to `Ed25519`.
  * The built-in synchronous password hashing at the ORM level of the advanced-alchemy library was moved to a `ThreadPoolExecutor(max_workers=2)`. The value `max_workers=2` was chosen strictly for the 2 physical cores of the test bench (running the Uvicorn server with core affinity to 0,1).

**Preliminary Analysis of Event Loop Blocking:**
*Before proceeding to analyze the flame graphs from the `py-spy` profiler and load testing, we will switch `asyncio` to `debug` mode at the FastAPI application level to record event loop slowdowns at runtime:*

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Enable asyncio debug mode
    loop = asyncio.get_running_loop()
    loop.set_debug(True)
    # Set the threshold to 100 ms (0.1 sec)
    loop.slow_callback_duration = 0.1
    yield
```

**Results of logging "heavy" callbacks:**
* **`/api/v1/access/signup`**: Thread blocking during synchronous password hashing was **~150 ms**.
* **`/api/v1/access/signin`**: The total blocking time for password verification and the sequential issuance of an access/refresh token pair reaches **~350–400 ms** (of which: password verification — **~150 ms**, token generation — **~250 ms**).

**Note:** The figures provided are Wall-clock time (total astronomical delay time) recorded by `asyncio debug`. This is not pure cryptography mathematics in a vacuum, but the total time during which the main Python thread was monopolized by computations without returning control to the Event Loop. These measurements serve as a clear demonstration of how heavy CPU-bound code paralyzes the asynchronous runtime.

#### Flame Graph Analysis
* **Conditions:**
  * **Application Server:** Uvicorn, 1 worker, mapped to 1 physical module (core 0).
  * **py-spy (`record` mode, no core affinity) | wrk2 (mapped to 1 physical module (core 7))**:
    * Endpoint `/api/v1/access/signup`: py-spy -> `--rate 100`; wrk2 -> RPS 4, 1 threads.
    * Endpoint `/api/v1/access/signin`: py-spy -> `--rate 100` (increased to 150 after optimization); wrk2 -> RPS 2, 1 threads.
    * Endpoint `/api/v1/access/me`: py-spy -> `--rate 150`; wrk2 -> RPS 300, 1 threads.
  * **Docker containers:** PostgreSQL, PGBouncer (cores 2,3) | Valkey (cores 4,5) were running. `ulimit (nofile=65535)` was set for all containers.
  * OS limits were raised (see `OS Tuning`)


* **Baseline Analysis:**
  * Endpoint `/api/v1/access/signup`: The CPU time share for synchronous user password hashing was within **~22-25%**. The flame graph clearly shows a deep call stack from the ORM integration level (`advanced_alchemy/types/password...`) down to the low-level `argon2.low_level.hash_secret` library, which monopolizes CPU time within the main thread.
  * Endpoint `/api/v1/access/signin`: The flame graph shows the cumulative effect of blocking the Event Loop with two heavy CPU-bound operations within a single request. The share of synchronous password verification via `argon2.low_level.verify_secret` takes about **~10–12%** of the worker's CPU time. The main overhead in the execution profile is formed by the sequential issuance of a pair of JWT tokens (access/refresh) using the asymmetric RSA-2048 algorithm (`jwt.algorithms.prepare_key` / `encode_jwt`), taking up **~32–34%** of CPU time for each token (a total of ~66% of the entire graph width).
  * Endpoint `/api/v1/access/me`: Decoding and verifying the signature of the incoming JWT token using the asymmetric RSA-2048 algorithm (`decode_jwt` -> `pyjwt.verify`) takes about **~10–12%** of CPU time. At the same time, the layer for working with the Valkey cache backend and deserializing user data using `msgspec` take up a minimal share of the CPU.

**Artifacts:** [signup.svg](https://github.com/bizoxe/iron-track/blob/benchmarks/benchmarks/docs/assets/auth-serialization/signup.svg) | [signin.svg](https://github.com/bizoxe/iron-track/blob/benchmarks/benchmarks/docs/assets/auth-serialization/signup.svg) | [me.svg](https://github.com/bizoxe/iron-track/blob/benchmarks/benchmarks/docs/assets/auth-serialization/me.svg)

* **Analysis after the first optimization:**
  * Endpoint `/api/v1/access/signin`: The flame graph clearly shows two isolated towers. Synchronous password hashing (`Argon2id`), wrapped in the pwdlib interface, has completely moved out of the main Event Loop into a dedicated ThreadPoolExecutor (crypto_executor). Token generation and signing operations are completely absent from the profiling graph.
  * Endpoint `/api/v1/access/me`: Decoding and verifying the token signature via `joserfc` collectively take ~20-22% of CPU (compared to ~10-12% for `PyJWT`). The load is distributed between the computational verification of the cryptographic signature (verify) and the internal mechanisms of deserialization/claims validation (`deserialize_compact`, `validate_compact`). **As a primary working hypothesis, I assumed (analyzing the me-joserfc.svg graph)** that this increase is explained by the library's deep OOP layer (the `JWTClaimsRegistry` class), where the call to `.validate(claims)` leads to the creation of intermediate objects, dynamic validator lookup, and data type inspection, taking up a significant percentage of processor time.

**Important clarification on the results of the final profiling: (Endpoint `/api/v1/access/me`)**
Subsequent analysis of the flame graph after implementing the "fast-path" showed that the Python wrapper for claims validation (`exp`, `iat` check) itself created minimal overhead.
The main processor time in these ~20-22% is spent on the **mathematics of verifying the cryptographic signature of the Ed25519 algorithm**. Unlike the asymmetric RSA-2048, where verification with a public key is "free" for the processor, the Ed25519 algorithm requires equally heavy scalar computations for both signing and verification.
Thus, the manual "fast-path" made the code cleaner and freed it from the library's unnecessary abstractions, but it was not possible to significantly reduce this ~20-22% CPU plateau on the `/api/v1/access/me` endpoint.

**Artifacts:** [signin-optimized.svg](https://github.com/bizoxe/iron-track/blob/benchmarks/benchmarks/docs/assets/auth-serialization/signin-optimized.svg) | [me-joserfc.svg](https://github.com/bizoxe/iron-track/blob/benchmarks/benchmarks/docs/assets/auth-serialization/me-joserfc.svg)

#### Hypothesis Confirmation
* **Endpoint `/api/v1/access/signup`:**
  * Flame Graph analysis (baseline) confirmed the hypothesis: `Argon2id` monopolizes the Event Loop.
  * System artifacts analysis: `sar` data confirms critical load on the scheduler during peak registration moments: `runq-sz` spikes up to 10 are recorded, which significantly exceeds the number of allocated cores and indicates a state of acute CPU time deficit (resource contention). The high level of `cswch/s` (up to ~5335) indicates excessive context switching caused by the OS's attempts to process incoming requests while the main Event Loop is blocked by synchronous `Argon2id` computations ([sar-logs](https://github.com/bizoxe/iron-track/blob/benchmarks/benchmarks/results/auth-serialization/test-signup/baseline/sar-metrics/reports/system.txt)).
* **Endpoint `/api/v1/access/signin`:**
  * Flame Graph analysis (baseline) partially confirmed my hypothesis: The Event Loop blocking is cumulative. Although password verification (`Argon2id`) makes a significant contribution, the main load is generated by the sequential generation of JWT tokens via RSA-2048.
  * System artifacts analysis: `sar` data confirms that during authentication, the system enters a "pulsating" load mode: alternating periods of deep Event Loop blocking (generating RSA signatures) and sharp processing bursts (processing the accumulated queue). Spikes in `runq-sz` to 10 and `cswch/s` to ~6592 clearly illustrate the degradation of response time when several CPU-bound tasks are executed simultaneously ([sar-logs](https://github.com/bizoxe/iron-track/blob/benchmarks/benchmarks/results/auth-serialization/test-signin/baseline/sar-metrics/reports/system.txt)).
* **Endpoint `/api/v1/access/me`:**
  * Flame Graph analysis (baseline) confirmed the hypothesis: Decoding and verifying the cryptographic signature of access tokens take significantly more processor time than deserializing user data. The flame graph analysis is self-sufficient to confirm the hypothesis.

*The methodology for the runs (wrk2) and sar metric collection are described below.*

#### Tests
* **Conditions:**
  * **Run methodology**: Before the start of each test series (Baseline / Optimization), the database was completely cleared. Testing was performed as a series of 4 consecutive runs: the first to record system metrics (sar), the subsequent three to average the performance results. The total size of the `user_account` table within one series did not exceed 1000 records.
  * **wrk2 (cores 6,7)**:
    * Endpoint `/api/v1/access/signup`: 5 RPS, 2 threads and 4 connections.
    * Endpoint `/api/v1/access/signin`: 3 RPS, 2 threads and 4 connections.
    * Endpoint `/api/v1/access/me`: 600 RPS, 2 threads and 4 connections.
  * **Application Server:** Uvicorn, 2 workers, mapped to 1 physical module (cores 0,1).
  * **Docker containers:** PostgreSQL, PGBouncer (cores 2,3) | Valkey (cores 4,5) were running. `ulimit (nofile=65535)` was set for all containers.
  * OS limits were raised (see `OS Tuning`)

#### Tables with baseline and first optimization results

**Technical note:** For an objective assessment of efficiency, we rely on **Mean Latency**, **P90**, and **CPU Load** (see `Justification for the relevance of wrk2 metrics`).

#### Endpoint `/api/v1/access/signup`

| Metric                | **Baseline** | **Optimization 1** | **Difference (Delta)**  |
|-----------------------|--------------|--------------------|-------------------------|
| **Mean Latency**      | 662.76 ms    | 656.63 ms          | **-0.9% (-6.13 ms)**    |
| **P90 (90%)**         | 674.30 ms    | 679.93 ms          | **+0.8% (+5.63 ms)**    |
| **P99 (99%)**         | 679.93 ms    | 684.54 ms          | **+0.7% (+4.61 ms)**    |
| **StdDev**            | 9.79 ms      | 24.50 ms           | **+150.3% (+14.71 ms)** |
| **Max Latency**       | 682.50 ms    | 684.54 ms          | **+0.3% (+2.04 ms)**    |
| **CPU Load (Core 0)** | 57.55%       | 58.29%             | **+0.74%**              |
| **CPU Load (Core 1)** | 57.66%       | 58.41%             | **+0.75%**              |

**Conclusion (Architectural isolation via ThreadPoolExecutor):** We observe no change in CPU load and `P90/Mean Latency`, as the computational complexity of `Argon2id` remained the same. The optimization here brought an exclusively *architectural* benefit — isolating the Event Loop from blocking.

**Baseline artifacts:** [wrk2-logs directory](https://github.com/bizoxe/iron-track/tree/benchmarks/benchmarks/results/auth-serialization/test-signup/baseline/wrk2-logs) | [sar-metrics directory](https://github.com/bizoxe/iron-track/tree/benchmarks/benchmarks/results/auth-serialization/test-signup/baseline/sar-metrics)

**Optimization 1 artifacts:** [wrk2-logs directory](https://github.com/bizoxe/iron-track/tree/benchmarks/benchmarks/results/auth-serialization/test-signup/optimization-01/wrk2-logs) | [sar-metrics directory](https://github.com/bizoxe/iron-track/tree/benchmarks/benchmarks/results/auth-serialization/test-signup/optimization-01/sar-metrics)

### Endpoint `/api/v1/access/signin`

| Metric                | **Baseline**       | **Optimization 1** | **Difference (Delta)**  |
|-----------------------|--------------------|--------------------|-------------------------|
| **Mean Latency**      | 857.39 ms          | 664.35 ms          | **-22.5% (-193.04 ms)** |
| **P90 (90%)**         | 1100.00 ms (1.10s) | 689.15 ms          | **-37.4% (-410.85 ms)** |
| **P99 (99%)**         | 1100.00 ms (1.10s) | 693.76 ms          | **-36.9% (-406.24 ms)** |
| **StdDev**            | 227.92 ms          | 26.36 ms           | **-88.4% (-201.56 ms)** |
| **Max Latency**       | 1110.00 ms (1.11s) | 704.51 ms          | **-36.5% (-405.49 ms)** |
| **CPU Load (Core 0)** | 58.76%             | 35.88%             | **-22.88%**             |
| **CPU Load (Core 1)** | 59.04%             | 35.68%             | **-23.36%**             |

**Conclusion (Changing token signing cryptography):** We observe a pure *computational* benefit. The drop in CPU utilization on cores 0 and 1 from 58% to 35% and the corresponding decrease in `Mean/P90 Latency` directly confirm that abandoning the resource-intensive RSA-2048 eliminated the main bottleneck of the endpoint.

**Baseline artifacts:** [wrk2-logs directory](https://github.com/bizoxe/iron-track/tree/benchmarks/benchmarks/results/auth-serialization/test-signin/baseline/wrk2-logs) | [sar-metrics directory](https://github.com/bizoxe/iron-track/tree/benchmarks/benchmarks/results/auth-serialization/test-signin/baseline/sar-metrics)

**Optimization 1 artifacts:** [wrk2-logs directory](https://github.com/bizoxe/iron-track/tree/benchmarks/benchmarks/results/auth-serialization/test-signin/optimization-01/wrk2-logs) | [sar-metrics directory](https://github.com/bizoxe/iron-track/tree/benchmarks/benchmarks/results/auth-serialization/test-signin/optimization-01/sar-metrics)

### Endpoint `/api/v1/access/me`

| Metric                | **Baseline** | **Optimization 1** | **Difference (Delta)** |
|-----------------------|--------------|--------------------|------------------------|
| **Mean Latency**      | 3.70 ms      | 4.23 ms            | **+14.3% (+0.53 ms)**  |
| **P90 (90%)**         | 4.36 ms      | 4.61 ms            | **+5.7% (+0.25 ms)**   |
| **P99 (99%)**         | 5.27 ms      | 5.73 ms            | **+8.7% (+0.46 ms)**   |
| **StdDev**            | 0.55 ms      | 0.43 ms            | **-21.8% (-0.12 ms)**  |
| **Max Latency**       | 7.92 ms      | 7.44 ms            | **-6.1% (-0.48 ms)**   |
| **CPU Load (Core 0)** | 44.56%       | 54.30%             | **+9.74%**             |
| **CPU Load (Core 1)** | 45.12%       | 54.26%             | **+9.14%**             |

**Conclusion (Changing cryptography for decoding/verifying token signatures):** We do not observe a critical drop in response time, but after optimization, there is an increase in CPU load (~9.5%). When analyzing the flame graph [me-joserfc.svg](https://github.com/bizoxe/iron-track/blob/benchmarks/benchmarks/docs/assets/auth-serialization/me-joserfc.svg), I hypothesized that validation via the `JWTClaimsRegistry` class introduces significant overhead. The `get_current_user` dependency is called in all protected endpoints, so it makes sense to get rid of validation via `JWTClaimsRegistry` in favor of a manual "fast-path" branching.

**Technical note:** In the final optimization, validation via the `JWTClaimsRegistry` class was removed. Subsequent profiling via py-spy and flame graph analysis showed that my assumption about the impact of `JWTClaimsRegistry` was incorrect. The main CPU time is spent on verifying token signatures.

**Baseline artifacts:** [wrk2-logs directory](https://github.com/bizoxe/iron-track/tree/benchmarks/benchmarks/results/auth-serialization/test-me/baseline/wrk2-logs) | [sar-metrics directory](https://github.com/bizoxe/iron-track/tree/benchmarks/benchmarks/results/auth-serialization/test-me/baseline/sar-metrics)

**Optimization 1 artifacts:** [wrk2-logs directory](https://github.com/bizoxe/iron-track/tree/benchmarks/benchmarks/results/auth-serialization/test-me/optimization-01/wrk2-logs) | [sar-metrics directory](https://github.com/bizoxe/iron-track/tree/benchmarks/benchmarks/results/auth-serialization/test-me/optimization-01/sar-metrics)

**Preliminary summary:** We implemented offloading of password hashing and verification to a `ThreadPoolExecutor` and migrated the token signing algorithm from RSA-2048 to Ed25519, thereby eliminating the blocking of the Event Loop by heavy computational operations. We recorded an unexpected increase in processor time for decoding and verifying token signatures when switching to the `joserfc` library via the flame graph.

**Main conclusion (Event loop blocking):** In the case of using an asynchronous wrapper (offloading) for password hashing/verification, the mathematics itself has not disappeared. For a single isolated user, the response on the `signup`/`signin` endpoints even slightly increased compared to the synchronous approach, as overhead was added for the context and management of the thread pool itself.
But we got an *architectural benefit on the scale of the entire system*:
With synchronous hashing, the event loop is monopolistically blocked for the entire duration of the calculations, which means the server worker is physically unable to process parallel requests from other clients — the system gets queued up. Moving this logic to a thread leaves the Event Loop free. A specific heavy request waits for its turn in the pool, but the server continues to process light/medium traffic in parallel and without delay on the same worker.

## Bottleneck Analysis Test (Point 4)

### Intermediate Test: Evaluating Serialization Efficiency (`FastAPI + Pydantic` vs. `msgspec`)

#### Theoretical Premise
Using FastAPI's standard response with a Pydantic model out-of-the-box involves the `json.dumps` serializer from the Python standard library (or Pydantic's built-in mechanisms), which require more CPU cycles for validation and transformation of complex types (e.g., `UUID`, `datetime`) compared to native `msgspec.json`. A custom `MsgSpecJSONResponse` implementation allows data to be serialized directly into bytes, eliminating the intermediate overhead of the standard mechanism.

#### Test Objective
Compare the serialization efficiency of the standard FastAPI mechanism and a custom implementation (`msgspec.Struct` + `MsgSpecJSONResponse` with native `msgspec.json`) on a real data profile.

#### Test Description
* **Implementation:**
  * Two models with identical fields were implemented: `ExerciseReadPydantic` and `ExerciseReadStruct`, which have complex types (`UUID`, `datetime`) and nested objects.
  * Two endpoints were implemented: `GET /serialization-pydantic` and `GET /serialization-msgspec`.
  * Both endpoints return the same dataset: `list[ExerciseReadPydantic]` | `list[ExerciseReadStruct]` of 50 objects.
  * To eliminate the influence of database I/O on Latency, no database query was performed.
* **Conditions:**
  * **Approach 1 (out-of-the-box):** FastAPI + `Pydantic` model (returned via the framework's standard JSON response).
  * **Approach 2 (custom):** `msgspec.Struct` + custom `MsgSpecJSONResponse` class.
  * **wrk2**: 600 RPS, 2 threads and 6 connections, mapped to 1 physical module (cores 6,7).
  * **Application Server:** Uvicorn, 2 workers, mapped to 1 physical module (cores 0,1).
  * **Docker containers:** No Docker containers were running.
  * Open file limits have been increased (`ulimit -n 65535`).

#### Comparison Summary

| Metric                | **msgspec** | **Pydantic v2** | **Difference (Delta)**   |
|-----------------------|-------------|-----------------|--------------------------|
| **Mean Latency**      | 1.72 ms     | 7.73 ms         | **+349.4% (+6.01 ms)**   |
| **P90 (90%)**         | 2.52 ms     | 9.01 ms         | **+257.5% (+6.49 ms)**   |
| **P99 (99%)**         | 2.99 ms     | 69.76 ms        | **+2233.1% (+66.77 ms)** |
| **StdDev**            | 0.55 ms     | 10.15 ms        | **+1745.5% (+9.60 ms)**  |
| **Max Latency**       | 3.71 ms     | 90.24 ms        | **+2332.3% (+86.53 ms)** |
| **CPU Load (Core 0)** | 11.66%      | 63.40%          | **+443.7%**              |
| **CPU Load (Core 1)** | 11.72%      | 64.36%          | **+449.1%**              |

**Technical note:** For an objective assessment of computational efficiency, we rely on **Mean Latency**, **P90**, and **CPU Load**, which better reflect the actual load on the system (see `Justification for the relevance of wrk2 metrics`).

**Conclusion:** The difference in speed between the libraries on the current hardware is in the range of 4-5 times in favor of `msgspec`. The difference in CPU Load (11.7% vs 64%) confirms that `msgspec` uses computational resources much more efficiently, which is an important factor for service scalability under high load.

**Artifacts:** [Source code](https://github.com/bizoxe/iron-track/blob/benchmarks/benchmarks/ext/auth-serialization/serialization.py) | [wrk2-logs directory](https://github.com/bizoxe/iron-track/tree/benchmarks/benchmarks/results/auth-serialization/test-serialization) | [sar-metrics directory](https://github.com/bizoxe/iron-track/tree/benchmarks/benchmarks/results/auth-serialization/test-serialization/sar-metrics)

### Test of `jsonable_encoder`'s impact on serialization (`MsgSpecJSONResponse (msgspec.json)`)
* **Implementation and Conditions:**
  * A `Pydantic` model was implemented: `ExerciseReadPydantic`, which has complex types (`UUID`, `datetime`) and nested objects.
  * Two endpoints were implemented:
    * `GET /serialization-pydantic` - standard `FastAPI` serialization mechanism.
    * `GET /serialization-jsonable-encoder` - serialization via the `MsgSpecJSONResponse` class (`jsonable_encoder` -> `msgspec.json`).
  * Both endpoints return the same dataset: `list[ExerciseReadPydantic]` of 50 objects.
  * To eliminate the influence of database I/O on Latency, no database query was performed.
  * **wrk2**: 600 RPS, 2 threads and 6 connections, mapped to 1 physical module (cores 6,7).
  * **Application Server:** Uvicorn, 2 workers, mapped to 1 physical module (cores 0,1).
  * **Docker containers:** No Docker containers were running.
  * Open file limits have been increased (`ulimit -n 65535`).

#### Test Results
* The test results for the `GET /serialization-pydantic` endpoint can be found in the section above: Evaluating Serialization Efficiency (`FastAPI + Pydantic` vs. `msgspec`).
* Testing the `GET /serialization-jsonable-encoder` endpoint at 600 RPS and 6 connections led to a critical performance degradation: response times increased to second-long values, indicating throughput saturation. A series of tests showed that this endpoint can handle the load without degradation at a significantly lower RPS: ~150 and 4 connections.

**Hypothesis partially confirmed:** An increase in latency and CPU load was expected, and the overhead of `jsonable_encoder` was supposed to be smoothed out by the `msgspec` library. During the tests, it was found that `jsonable_encoder` introduces significant overhead. Additional testing and profiling via py-spy are pointless.

**Conclusion:** The call to `jsonable_encoder` needs to be removed from the current implementation of the `MsgSpecJSONResponse` class and switched to native serialization (`msgspec.json`). This will require having two schemas in the project: Pydantic for "input" (validation), and `msgspec.Struct` for "output" (serialization).
Having multiple schemas complicates project maintenance but is compensated by scalability under high loads.

**Artifacts:** [Source code](https://github.com/bizoxe/iron-track/blob/benchmarks/benchmarks/ext/auth-serialization/serialization.py) | [wrk2-logs directory](https://github.com/bizoxe/iron-track/tree/benchmarks/benchmarks/results/auth-serialization/test-serialization/test-jsonable_enc)

## Bottleneck Analysis Tests (Points 1 to 3 inclusive) Final Optimization
This optimization includes the changes made in the first stage:

* Isolation of password hashing via `ThreadPoolExecutor`, but now with explicit fixing of **`Argon2id`** parameters (`parallelism=1`, `time_cost=3`, `memory_cost=65536`). Although the time and memory remained at their default values, forcing `parallelism=1` protects the CPU from context switching under high load by preventing the algorithm from spawning 4 computational threads.
* Changing the **PyJWT** library to **joserfc** and the token signing algorithm from `RSA-2048` to `Ed25519`.

**Key Changes:**

* **Endpoint `/api/v1/access/signup`:**
* **ORM-level optimization:** The `auto_refresh=False` parameter was introduced when calling the user creation method in `advanced-alchemy`. This eliminated the redundant hidden `SELECT` query (a repeated round-trip to the DB) after the `INSERT` operation, as all necessary auto-generated fields are read from the session context.
* **Transport layer optimization:** A complete rejection of Pydantic models on the output layer in favor of `msgspec.Struct` structures. Instead of the standard FastAPI serializer, the native `MsgSpecJSONResponse` was used, which completely eliminated the heavy `jsonable_encoder` from the serialization process.


* **Endpoint `/api/v1/access/signin`:**
* **Elimination of redundant queries and limitation of field selection (ORM layer):** In the `UserService.authenticate` method, the data loading strategy was optimized. The `noload(m.User.role)` directive was applied, which canceled the default `selectinload` strategy for this relationship. The `load_only` directive was also used, limiting the initial query to the `user_account` table to strictly the fields necessary for validation (`id`, `email`, `is_active`, `password`).


* **Endpoint `/api/v1/access/me`:**
* **Elimination of redundant queries and limitation of field selection (ORM layer):** In the `_get_user_from_payload` method, the data loading strategy was optimized. Instead of two separate queries (the primary one to the user and the automatic `selectinload` to their role), a single SQL query with a `LEFT JOIN` via `joinedload(User.role)` is now executed. At the same time, `load_only` at both levels limits the selection to the absolute minimum (`Role.slug` and 5 basic user fields).
* **Transport layer optimization:** The `UserAuth` transport model was replaced from Pydantic to a lightweight `msgspec.Struct` structure.
* **Switch to In-Memory Caching:** The `fastapi-cache2` library was replaced with `cashews` with local caching enabled (`client_side=True`).
* **Refactoring the validation layer:** Token validation via the `JWTClaimsRegistry` class in the `get_payload_from_token` function was replaced with a straightforward manual "fast-path".



**Flame graph analysis after removing `JWTClaimsRegistry`:** A comparison of the [me-joserfc.svg](https://github.com/bizoxe/iron-track/blob/benchmarks/benchmarks/docs/assets/auth-serialization/me-joserfc.svg) and [me-final.svg](https://github.com/bizoxe/iron-track/blob/benchmarks/benchmarks/docs/assets/auth-serialization/me-final.svg) profiles shows that removing `JWTClaimsRegistry` eliminated the small "fringe" of Python calls at the tails of the `validate_compact` function, making the stack structure flat. However, the width of the entire JWT branch remained unchanged (~21%). This clearly proves: the overhead from Python's object abstractions in this node was close to zero, and all the CPU utilization is the pure mathematics of the Ed25519 algorithm, which can only be bypassed architecturally (by caching). From this, it follows that my assumption about the influence of `JWTClaimsRegistry` is incorrect.

**Key architectural shift (Caching access tokens):** Despite the fact that point optimization removed the OOP overhead of Python, the endpoint continues to be limited by the mathematics of verifying the Ed25519 cryptographic signature. The optimal solution will be to cache valid tokens by their `jti`.

**General conclusion on token cryptography:**
During the tests, we encountered an architectural paradox of cryptography. The asymmetric **RSA-2048** algorithm turned out to be heavy when generating tokens (signing), but when validating (decoding/verifying), in contrast to the modern Ed25519, it suddenly became faster and "lighter".

**Flame graph analysis of access token caching:** When analyzing the [me-cached.svg](https://github.com/bizoxe/iron-track/blob/benchmarks/benchmarks/docs/assets/auth-serialization/me-cached.svg) flame graph, the cryptographic signature (Ed25519), which previously took ~20-22% of processor time, is no longer a bottleneck (the CPU-bound operation has been removed).
A shift in load is observed: to the IO-bound area (waiting for data) and the application's business logic. Deserializing the access token takes ~5% of processor time, deserializing user data ~6%.

**Summary:** Thanks to the introduction of token caching by jti, the CPU load during validation has been reduced from ~22% to zero (assuming a cache hit), moving the endpoint to an IO-bound state with a total CPU cost for deserialization of ~11%.

**The fundamental difference between the two algorithms is explained below:**

<details>
<summary><b>Security Performance Analysis: RSA-2048 vs Ed25519</b></summary>

* The RSA algorithm is **asymmetric** not only in its key logic but also in its computational load.
* **Signing (Private Key):** The processor raises a number to the giant power of a 2048-bit secret exponent $d$. This involves thousands of heavy multiplication cycles of large numbers, which heavily burn the CPU when issuing tokens.
* **Verification (Public Key):** Here, a global constant is used — a fixed small number **`65537`** ($2^{16} + 1$). To raise the token matrix to this power, the processor needs to perform only **17 simple multiplications** using the binary exponentiation algorithm.



**Profiling summary:** Despite the fact that the RSA signature verification operation is mathematically cheap, the full JWT processing stack (parsing, decoding, cryptographic verification) in the baseline version consumes ~10–12% of processor time on the endpoint.

* Ed25519 algorithm: there is no exponentiation to giant powers; all work is based on **scalar multiplication of points on a curve**.
* **Signing (Private Key):** The algorithm multiplies a fixed base point of the curve. For it, pre-computation tables ("cheat sheets") are pre-wired into the libraries. The processor digests this task instantly, and issuing tokens ceases to be a bottleneck.
* **Verification (Public Key):** The processor needs to perform **two scalar multiplications** at once. One of them is for the public key, for which it is impossible to pre-compile a "cheat sheet" in memory. The processor is forced to unwind the full mathematics of the elliptic curve from scratch.



**Profiling summary:** The Ed25519 verification operation mathematically requires more processor cycles than RSA-2048 verification. This is confirmed by the increase in CPU time from ~12% to ~22%. However, it was this transition that made it possible to completely move away from "heavy" RSA operations at the token generation stage (signing) in other parts of the system. In the context of the /me endpoint, we compensated for this cryptographic overhead by introducing caching by jti, turning a CPU-bound operation into an IO-bound one and achieving an overall reduction in processor time of ~11%.

</details>

### The tables below include the results of the baseline, first, and final optimization tests

**Technical note:** For an objective assessment of efficiency, we rely on **Mean Latency**, **P90**, and **CPU Load** (see `Justification for the relevance of wrk2 metrics`).

**Note:** Before starting the final series of runs, the database was cleared.

#### Endpoint `/api/v1/access/signup`

| Metric                | **Baseline** | **Optimization 1** | **Final**     | **Delta (Baseline → Final)**  |
|-----------------------|--------------|--------------------|---------------|-------------------------------|
| **Mean Latency**      | 662.76 ms    | 656.63 ms          | **601.42 ms** | **-9.26% (-61.34 ms)**        |
| **P90 (90%)**         | 674.30 ms    | 679.93 ms          | **654.34 ms** | **-2.96% (-19.96 ms)**        |
| **P99 (99%)**         | 679.93 ms    | 684.54 ms          | **662.02 ms** | **-2.63% (-17.91 ms)**        |
| **StdDev**            | 9.79 ms      | 24.50 ms           | **52.76 ms**  | **+438.9% (+42.97 ms)**       |
| **Max Latency**       | 682.50 ms    | 684.54 ms          | **661.50 ms** | **-3.08% (-21.00 ms)**        |
| **CPU Load (Core 0)** | 57.55%       | 58.29%             | **55.46%**    | **-3.63% (-2.09%)**           |
| **CPU Load (Core 1)** | 57.66%       | 58.41%             | **56.51%**    | **-2.00% (-1.15%)**           |

**Brief analysis:** A decrease in Mean Latency of ~9% and a slight decrease in CPU load are observed (Delta Baseline → Final).
The introduction of the `auto_refresh=False` parameter at the ORM level and the switch to native `msgspec.json` serialization in the final optimization provided a performance boost. However, the dominant factor (P90/P99) remains the `Argon2id` cryptography.
It should be noted that a small amount of data is serialized on this endpoint, and the difference between the custom implementation and the standard serialization of the FastAPI framework is not so obvious in this case.

**Final optimization artifacts:** [wrk2-logs directory](https://github.com/bizoxe/iron-track/tree/benchmarks/benchmarks/results/auth-serialization/test-signup/final/wrk2-logs) | [sar-metrics directory](https://github.com/bizoxe/iron-track/tree/benchmarks/benchmarks/results/auth-serialization/test-signup/final/sar-metrics)

#### Endpoint `/api/v1/access/signin`

| Metric                | **Baseline** | **Optimization 1** | **Final**     | **Delta (Baseline → Final)**  |
|-----------------------|--------------|--------------------|---------------|-------------------------------|
| **Mean Latency**      | 857.39 ms    | 664.35 ms          | **520.95 ms** | **-39.2% (-336.44 ms)**       |
| **P90 (90%)**         | 1100.00 ms   | 689.15 ms          | **676.86 ms** | **-38.5% (-423.14 ms)**       |
| **P99 (99%)**         | 1100.00 ms   | 693.76 ms          | **683.52 ms** | **-37.9% (-416.48 ms)**       |
| **StdDev**            | 227.92 ms    | 26.36 ms           | **110.52 ms** | **-51.5% (-117.40 ms)**       |
| **Max Latency**       | 1110.00 ms   | 704.51 ms          | **686.08 ms** | **-38.2% (-423.92 ms)**       |
| **CPU Load (Core 0)** | 58.76%       | 35.88%             | **33.31%**    | **-43.3% (-25.45%)**          |
| **CPU Load (Core 1)** | 59.04%       | 35.68%             | **34.18%**    | **-42.1% (-24.86%)**          |

**Brief analysis:** In the final optimization, the loading strategy was changed: limiting the selection of `User` model fields and applying the `noload(m.User.role)` directive. A decrease in Mean Latency of ~39% is observed (Delta Baseline → Final). Although ORM optimization improved the average latency by reducing I/O and memory overhead, the tail latencies P90/P99 between the first and final optimizations show diminishing returns.
As with the `/api/v1/access/signup` endpoint, the determining factor remains the `Argon2id` cryptography.

**Final optimization artifacts:** [wrk2-logs directory](https://github.com/bizoxe/iron-track/tree/benchmarks/benchmarks/results/auth-serialization/test-signup/final/wrk2-logs) | [sar-metrics directory](https://github.com/bizoxe/iron-track/tree/benchmarks/benchmarks/results/auth-serialization/test-signup/final/sar-metrics)

#### Endpoint `/api/v1/access/me`

| Metric                | **Baseline** | **Optimization 1** | **Final**   | **Delta (Baseline → Final)** |
|-----------------------|--------------|--------------------|-------------|------------------------------|
| **Mean Latency**      | 3.70 ms      | 4.23 ms            | **2.35 ms** | **-36.5% (-1.35 ms)**        |
| **P90 (90%)**         | 4.36 ms      | 4.61 ms            | **3.01 ms** | **-31.0% (-1.35 ms)**        |
| **P99 (99%)**         | 5.27 ms      | 5.73 ms            | **3.90 ms** | **-26.0% (-1.37 ms)**        |
| **StdDev**            | 0.55 ms      | 0.43 ms            | **0.51 ms** | **-7.3% (-0.04 ms)**         |
| **Max Latency**       | 7.92 ms      | 7.44 ms            | **4.91 ms** | **-38.0% (-3.01 ms)**        |
| **CPU Load (Core 0)** | 44.56%       | 54.30%             | **28.93%**  | **-35.1% (-15.63%)**         |
| **CPU Load (Core 1)** | 45.12%       | 54.26%             | **30.19%**  | **-33.1% (-14.93%)**         |

**Brief analysis:** During the first optimization, it was found that verifying access token signatures via the `Ed25519` algorithm introduces significant overhead. Optimization was performed at the transport and ORM layers. However, a significant performance boost and reduction in CPU load occurred due to local caching of access tokens (see flame graph analysis `me-cached.svg`).

**Final optimization artifacts:** [wrk2-logs directory](https://github.com/bizoxe/iron-track/tree/benchmarks/benchmarks/results/auth-serialization/test-signup/final/wrk2-logs) | [sar-metrics directory](https://github.com/bizoxe/iron-track/tree/benchmarks/benchmarks/results/auth-serialization/test-signup/final/sar-metrics)

---

> *The section below presents additional benchmarks and profiling results. The studies are intended to quantify infrastructure overhead (logging), as well as to demonstrate the effect of changing scheduler parameters (`random_page_cost`) on PostgreSQL query performance.*

### Additional point: The impact of structured logging on latency

#### 1. Theoretical premise
Structured logging using `StructLogMiddleware` requires additional I/O operations and processor time (calculating time, extracting headers, forming a JSON structure).

#### 2. Test objective
The purpose of this test is to determine the overhead that logging middleware adds to the life cycle of each application request using the example of the most lightweight endpoint.

#### 3. Test description
* **Endpoint:** `GET /ping` (returns `PlainTextResponse`, `b"OK"`).
* **Conditions:**
  * Without using `StructLogMiddleware` (pure FastAPI).
  * With `StructLogMiddleware` enabled, format `json`.
  * **wrk2**: 1000 RPS, 2 threads and 10 connections, mapped to 1 physical module (cores 6,7).
  * **Application Server:** Uvicorn, 2 workers, mapped to 1 physical module (cores 0,1).
  * To eliminate the influence of rendering Uvicorn logs in the terminal, the output was redirected to `/dev/null`.
  * **Docker containers:** No Docker containers were running.
  * Open file limits have been increased (`ulimit -n 65535`).

#### 4. Comparison summary

| Metric                | Pure Ping   | Ping + StructLog | Difference (Overhead)     |
|-----------------------|-------------|------------------|---------------------------|
| **Mean Latency**      | 2.26 ms     | 2.83 ms          | **+25.22% (+0.57 ms)**    |
| **P90 (90%)**         | 3.29 ms     | 3.56 ms          | **+8.21% (+0.27 ms)**     |
| **P99 (99%)**         | 4.12 ms     | 4.41 ms          | **+7.04% (+0.29 ms)**     |
| **StdDev**            | 0.78 ms     | 3.01 ms          | **+285.90% (+2.23 ms)**   |
| **Max Latency**       | 5.26 ms     | 82.37 ms         | **+1465.97% (+77.11 ms)** |
| **CPU Load (Core 0)** | 23.43%      | 38.44%           | **+64.06%**               |
| **CPU Load (Core 1)** | 24.01%      | 37.96%           | **+58.10%**               |

**Technical note:** For an objective assessment of efficiency, we rely on **Mean Latency**, **P90**, and **CPU Load** (see `Justification for the relevance of wrk2 metrics`).

**Conclusion:** If we compare Mean Latency/P90, logging hardly introduces any significant overhead (+0.57 ms/+0.27 ms). But looking at the CPU Load, we see an increase in load from ~24% to ~39%. This is +15% of the total core power (in absolute terms).

**Artifacts:** [wrk2-logs directory](https://github.com/bizoxe/iron-track/tree/benchmarks/benchmarks/results/auth-serialization/test-ping) | [sar-metrics directory](https://github.com/bizoxe/iron-track/tree/benchmarks/benchmarks/results/auth-serialization/test-ping/sar-metrics)

#### 5. Flame Graph Analysis
* **Conditions:**
  * **py-spy**: `record` mode, `--rate 150`, mapped to 1 physical module (cores 2,3).
  * **wrk2**: 600 RPS, 2 threads and 4 connections, mapped to 1 physical module (cores 6,7).
  * **Application Server:** Uvicorn, 1 worker, mapped to 1 physical module (core 0).
  * Open file limits have been increased (`ulimit -n 65535`).

**Analysis:** [ping-with-logging.svg](https://github.com/bizoxe/iron-track/blob/benchmarks/benchmarks/docs/assets/auth-serialization/ping-with-logging.svg):
In total, non-blocking structured logging takes ~34% of processor time: ~23% is spent on the request passing through the FastAPI layers and executing the endpoint logic (`await self.app`), ~11% - forming the log and passing it to the non-blocking output (`logger.info`).
The figure of ~34% may seem huge, but it should be borne in mind that the profiler shows us the **share of time** spent in a particular node of the stack **relative to the total time** of a particular request.

**Here is an example:**
* For `/ping`: The middleware takes, say, 0.05 ms out of a total time of 0.2 ms → 23%.
* For `/signin`: The middleware takes the same 0.05 ms out of a total time of 500 ms → 0.01%.

Thus, the **absolute time** (CPU cost of executing the `StructLogMiddleware` code) is the same in both cases.

**Note on data interpretation:** The percentages shown reflect the relative cost of performing operations on a trivial endpoint. The absolute cost (Fixed Cost) of logging in this benchmark is ~0.57 ms (Mean Latency). As the business logic of the endpoint becomes more complex (e.g., when performing cryptographic operations or complex SQL queries), the relative contribution of logging will tend to <1%.

### Additional point: Analysis of DBMS configuration (I/O-bound)

#### 1. Theoretical premise
When working with a PostgreSQL DBMS on hard disk drives (HDDs), it is critically important to consider the physical limitations of the disk subsystem, in particular the delays that arise when moving the magnetic heads.

#### 2. Test objective
Let's compare the default value `random_page_cost=4.0` and `random_page_cost=1.0`, and how this affects the query planner (Cost-Based Optimizer) when working with a selection that makes up about 1% of the total table size (4937 rows out of 500,000).
The `exercises` table was chosen for the experiment. When comparing `random_page_cost=4.0` and `random_page_cost=1.0`, the `seq_page_cost` value was not changed (default `seq_page_cost=1.0`).
The queries and main (default) PostgreSQL settings can be viewed here: [postgresql-random-page-cost-analysis.md](https://github.com/bizoxe/iron-track/blob/benchmarks/benchmarks/docs/assets/resources/postgresql-random-page-cost-analysis.md).

**Note:** All measurements were made on data located in the cache (`shared buffers`). This was done to isolate the influence of the planner (Access Path) from the physical delay of reading from the disk, which allows for a clear demonstration of the decision-making logic of the optimizer (Cost-Based Optimizer).

#### 3. Comparison summary:
1. **Selection characteristics:**
   * Total table size: 500,000 rows.
   * Number of rows satisfying the condition (`is_system_default IS TRUE`): 4,937 (less than 1% of the total).

2. **With `random_page_cost = 4.0`:**
   * **Plan:** Bitmap Heap Scan.
   * **Execution Time:** 11.560 ms.
   * **Planner logic:** Due to the high cost of random data access (4.0), the planner decides to first build a bitmap and read the pages sequentially.
   * **Metrics:** `Buffers: shared hit=3861`

3. **With `random_page_cost = 1.0`:**
   * **Plan:** Index Scan.
   * **Execution Time:** 7.794 ms.
   * **Planner logic:** The cost of random access is equated to sequential access. The planner believes that reading through the index will be cheaper and more direct, which leads to a reduction in query execution time by almost 1.5 times.
   * **Metrics:** `Buffers: shared hit=3967`
