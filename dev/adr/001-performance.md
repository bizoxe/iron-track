# ADR-001: System Performance & Security Optimization

## Status
Accepted

## Date
2026-02-07

---

## Context

The system required a global revision of performance and stability to ensure consistent operation under constrained hardware conditions.

Infrastructure:

- **CPU:** AMD FX-8320 (Piledriver)
- **RAM:** 12 GB DDR3-1600
- **Disk:** HDD 7200 RPM
- **Stack:** Python 3.12, FastAPI, PostgreSQL 18

Observed problems:

- CPU saturation during RSA signing.
- Event loop blocking caused by synchronous Argon2 hashing.
- Lack of application-level memory cache (L1) caused excessive network round-trips to Redis on hot reads.
- Limited cache invalidation capabilities.
- Serialization overhead in FastAPI.
- PostgreSQL planner misestimating random I/O cost on HDD.

The goal was to improve performance without reducing cryptographic strength or architectural clarity.

---

## Decision

### 1. Migration to Ed25519 and joserfc

**Decision:** Replace `pyjwt (RSA-2048)` with `joserfc (Ed25519)`.

**Rationale:**

- **Performance:** RSA requires heavy computations and blocked CPU. Ed25519 is significantly faster with equivalent security.
- **DX & CI/CD:** joserfc enables single-command key generation, simplifying rotation and deployment without `.pem` files.
- **Standards:** Native JWK support and strict RFC compliance.

---

### 2. Cache Layer Replacement — cashews

**Decision:** Replace `fastapi-cache2` with `cashews` using Hybrid L1 + L2 caching.

**Architecture:**

- L1 — In-memory
- L2 — Redis

**Rationale:**

- fastapi-cache2 shows maintenance stagnation.
- Limited fine-grained invalidation (namespace wipes required).
- Built-in Cache Stampede protection (locking).
- Eliminated need for manual Redis dependency injection.
- Enabled L1 pre-cache for hot reads (e.g., user profile).

---

### 3. Async Password Hashing

**Decision:** Offload Argon2id hashing to a dedicated ThreadPoolExecutor to prevent Event Loop blocking.

**Configuration:**

- Executor: max_workers = max(min(cpu_count, 4), 1) (Restricts crypto-load to 50% of FX-8320 logical cores to keep the server responsive).
- Argon2id Parameters:
  - parallelism = 1 (Deterministic single-thread execution per hash).
  - time_cost = 3
  - memory_cost = 65536 (64 MB).

**Rationale:**

- Sync hashing blocked the event loop.
- Caused request timeouts under load.
- FX-8320 + DDR3 bandwidth constraints penalize parallel hashing.
- Parallelism = 1 prevents a cascade performance degradation (excessive context switching and memory bus contention) that occurs during the simultaneous operation of 8 workers. This minimizes contention for the shared DDR3 data bus and the shared L3 caches of the Piledriver architecture.

**Result:** Achieved linear latency stability and eliminated "Socket Errors" during peak registration bursts.

---

### 4. DTO Layer Split (Pydantic / msgspec.Struct)

**Decision:**

- Input → Pydantic (validation)
- Output → msgspec.Struct (serialization)

**Rationale:**

- Removed `jsonable_encoder`.
- Migrated to native `msgspec.json`.

**Performance Impact:**

- P99 latency on `/health` reduced from **859 ms → 128 ms** due to cumulative effect of msgspec serialization and reduced event loop contention.

**Trade-offs:**

- Two schema systems in codebase.
- Handlers must explicitly return `MsgSpecJSONResponse`.
- FastAPI defaults to Pydantic serialization if misconfigured.

---

### 5. PostgreSQL HDD Planner Tuning

**Decision:**

- random_page_cost = 3.0 (Default was 1.1)

**Rationale:**

- HDD random seek is expensive.
- Planner incorrectly preferred Index Scan.
- Caused degradation once dataset exceeded ~700 rows.

**Result:** Stable performance beyond 5 000 records.

---

## Performance Benchmarks

### Test 1 — POST /api/v1/access/signup  
Heavy CPU + DB load (Argon2id + writes, 5 000+ records)

| Metric        | Uvicorn (uvloop) | Granian (mt) | Notes                 |
|---------------|------------------|--------------|-----------------------|
| RPS           | 13.43            | 13.49        | CPU saturation peak   |
| Avg Latency   | 1.16 sec         | 1.14 sec     | Stable for Argon2id   |
| P99 Latency   | 1.86 sec         | 2.00 sec     | Within expected range |
| Socket Errors | 2–16             | 6            | Resource saturation   |

---

### Test 2 — GET /health  
I/O + MsgSpec serialization

SELECT 1 + Redis PING

| Metric        | Before (jsonable) | After (MsgSpec) | Gain             |
|---------------|-------------------|-----------------|------------------|
| RPS (Uvicorn) | 1615              | 1735            | +120 req/s       |
| Avg Latency   | ~78 ms            | 56.35 ms        | −28%             |
| P99 Latency   | ~859 ms           | 128.76 ms       | 6.5× improvement |

---

### Test 3 — GET /api/v1/access/me

JWT Decoding (Ed25519) + L1 Cache (Cashews) vs Old RSA + L2

| Metric        | RSA (Old Stack) | Ed25519 + L1 (New Stack) | Gain     |
|---------------|-----------------|--------------------------|----------|
| RPS (Uvicorn) | 1613.55         | 2392.52                  | +48.3%   |
| Avg Latency   | 60.07 ms        | 41.39 ms                 | −31.1%   |
| P99 Latency   | 143.95 ms       | 140.82 ms                | Improved |

### Granian Note (GET /api/v1/access/me)

Granian requires warm-up.

- Initial: ~1800 RPS
- After 30s load: ~1960+ RPS

Still slightly behind Uvicorn on lightweight workloads due to thread orchestration overhead on FX architecture.

Full logs, reproduction commands, and execution history: See [benchmarks](../../benchmarks/BENCHMARKS.md).

---

## Hardware Constraints Analysis

### DDR3 Memory Bandwidth Impact

Argon2id (`memory_cost=65536`) creates significant RAM pressure.

On FX-8320:

- 8 cores / dual-channel DDR3
- Memory bandwidth becomes bottleneck
- >4 hashing threads cause latency degradation
- CAS latency amplifies contention

**Conclusion:** `parallelism=1` provides most stable P99 latency.

---

### PostgreSQL Planner Impact

Before:

- random_page_cost = 1.1

Adjusted:

- random_page_cost = 3.0


**Effect:**

- Prevented inefficient Index Scan selection.
- Maintained ~13 RPS at 5 000+ rows.
- Previous degradation: 9–10 RPS.

---

## Consequences

### Positive

- Reduced JWT CPU cost.
- Stable latency under hashing load.
- Faster serialization.
- Fine-grained cache invalidation.
- HDD-aware query planning.

### Negative

- Dual DTO system complexity.
- Explicit response class requirements.
- Hardware-tuned DB settings require revision after SSD migration.
- Added executor management overhead.

---

## Alternatives Considered

### JWT

- RSA-2048 (RS256) → Heavy & Legacy.
- ECDSA (ES256) → Performance & Risk.
- HMAC (HS256) → Symmetric Security Risk.

### Cache

- fastapi-cache2 → Limited invalidation, lack of multi-layering (L1 + L2), no Cache Stampede protection.
- aiocache → Legacy maintenance, lack of native hybrid (L1+L2) chaining, complex custom invalidation.
- Custom Redis → High development overhead, manual serialization management.

### Serialization

- Pydantic only → Slower.
- orjson + dict → No schema guarantees.

### Hashing

- Sync Argon2 → Event loop blocking.
- bcrypt → Lower security profile.


