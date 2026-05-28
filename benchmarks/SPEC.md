## Specification: Load Testing & Profiling

**Abstract:**
> The proposed testing methodology and choice of tools should not be perceived as an attempt to simulate production testing.
>
> In a production environment, even if you have locally identical hardware to what is in the cloud, local testing results will likely differ due to the specifics of the cloud infrastructure.
>
> All tests were conducted on a single host machine (one node, Loopback/Synthetic testing). The reason I chose this approach is that we are testing the application itself, not the network throughput, so the test results may be significantly higher.
>
> The choice of the test bench (FX-8320/HDD) is due not only to its availability as a training base, but also to the fact that more powerful modern hardware can mask the shortcomings of the application code, making a less powerful bench more preferable for identifying bottlenecks.

### Test Bench Specification
* **Hardware & OS:** Debian 12 (Bare Metal Desktop Installation, Kernel 6.1.x)
* **Scope/Type:** Local benchmark
* **Deployment Topology:**
* **Configuration A (Isolated Profile):**
    * **Application (App):** Running on the host (Debian 12 Bare Metal) under **Granian/Uvicorn** (TCP/IP).
    * **Services (PostgreSQL, Valkey, PgBouncer):** Running in Docker containers.
* **Configuration B (Integrated Benchmark):**
    * **Application (App), proxy (Angie), and services (PostgreSQL, Valkey, PgBouncer):** Running as a single bundle in Docker containers. The application runs under **Granian** (uses UDS to interact with Angie).


**Hardware Resources:**

* **CPU:** AMD FX-8320 (8 cores, 8 threads)
* **Memory:** 12 GB DDR3
* **Storage:** HDD 7200 RPM (SATA III)

**Software Stack:**

* **Python:** 3.12.6
* **Databases & Services:** PostgreSQL 18.3, PgBouncer 1.23.1, Valkey 8.0.6, Angie 1.11.0
* **Application Servers:** Granian 2.7.0, Uvicorn 0.40.0


**Benchmarking & Observability Tools:**

* **Load Generation (`wrk2`):** Generating constant load with latency control; analysis of final performance reports.
* **System Monitoring (`sar`):** Collecting system metrics (CPU, I/O, Network) for correlation with load.
* **Profiling (`py-spy`):** Profiling Python processes; building Flame Graphs to identify bottlenecks in the executable code.


**Application Server Flags:**

* **Granian:** `--interface`, `--workers`, `--runtime-threads`, `--runtime-mode`, `--loop`, `--backlog`.
* **Uvicorn:** `--workers`, `--loop`, `--http`, `--backlog`.

**Note:** The deployment topology, versions of infrastructure services, and versions of application servers may change. In this case, all information will be provided in the specific benchmarks.

### System Configuration
* [Basic OS settings are required before starting](./SETUP.md):
  * Increasing the open file limit (`ulimit`) and network buffer sizes.
  + Configuring system queues (`somaxconn`) and memory management parameters (`overcommit_memory`).

---

### Basic Concepts of Load Testing:
* **System Requirements:** Before starting the tests, the parameters from [SETUP.md](./SETUP.md) are applied (increasing `ulimit`, configuring `somaxconn`, `overcommit_memory`, and network buffers).
* **Load Generation:** `wrk2` is used with a fixed request rate (`-R`) instead of the classic `wrk` to prevent the *Coordinated Omission* effect.
* **Isolation and CPU Affinity (`taskset`):** Given the modular architecture of the AMD FX-8320 processor (where two cores share one FPU and L2 cache), processes are distributed across modules (**basic scheme**):
  * Module 0 (Cores 0-1): Application (FastAPI / Application Server (Granian/Uvicorn))
  * Module 1 (Cores 2-3): PostgreSQL + PgBouncer
  * Module 2 (Cores 4-5): Valkey
  * Module 3 (Cores 6-7): `wrk2` (Load Generator)
  * *Note:* The exact core distribution and affinity scheme is specific to the profile and is documented in the configuration of each specific test.
* **Power Management (CPU Governor):** Before starting the test, the processor is forcibly switched to maximum performance mode (`performance`) to eliminate delays associated with dynamic frequency scaling (DVFS).
* **Environment (OS Mode):** Tests are conducted in console mode (TTY) with the graphical server (display manager) stopped to eliminate background load on the CPU and memory bus.
* **Warm-up and Measurement Methodology (4 runs):**
  * **Run 1 (Warm-up):** The 1st run (5 seconds) is performed to warm up the caches (DB/Valkey), adapt the Python interpreter, and initialize the connection pool. The results are not taken into account.
  * **Runs 2–4 (Measurement):** 3 consecutive runs of 30 seconds each are conducted with a 20-second pause between runs.
  * **Stability Criterion:**
    * **Mean Latency:** The coefficient of variation (CV) between runs 2, 3, and 4 should be < 3%.
    * **P99 Latency:** The target CV is < 5%.
    * *Note:* Given the architectural features of the test bench (shared CPU cores), we will focus on Mean Latency.
* **Analysis:**
  * The results of the best of the stable runs are used for the report.
  * Focus on Tail Latency:
    * P99 and Max percentiles are analyzed as key metrics, reflecting the real user experience.
    * *Note:* During the load tests, system outliers were identified (see [Justification for the relevance of wrk2 metrics (System Jitter)](auth-serialization.md)). The test results will include Max Latency and P99 values. However, when analyzing the results, we will primarily focus on Mean Latency and P90 as the most representative metrics of stability under the conditions of the current test bench.
