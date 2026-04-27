# Tech Stack Rationale: IronTrack
**Format:** Technical Journal

**Status:** Decided

**Last updated:** April 2026

> **Quick Jump:** [RDBMS](#rdbms-selection) | [Conn Pooler](#connection-pooler-selection) | [ORM](#orm-selection) | [Web Layer](#web-layer-selection) | [In-Memory](#in-memory-storage-selection) | [Reverse Proxy](#reverse-proxy-selection)

### Abstract
This document outlines the reasoning behind my core infrastructure choices, including theoretical background (Theory subsection).

> **Note:** Some sections may describe concepts in detail that seem fundamental to experienced engineers. This is intentional for the completeness of the technical context and personal systematization of the stack's key features.

---

## RDBMS Selection

#### CONTEXT
RDBMS Selection Criteria (Derived from Database Schema Blueprint):
- Ensuring strict relational integrity;
- Support for custom types (ENUM) and Timezones;
- Support for UUID v7 or mechanisms for storing sortable UUIDs;
- Ability to create complex unique indexes and index expressions (Functional Indexes);
- Presence of advanced constraints (Check Constraints);
- Analytical capabilities: Generated Columns, Window Functions, potential use of trigger logic;
- Ability to efficiently store and search data in JSON format (considered as an extensible alternative for unstructured data);
- Ecosystem & Performance: native support for high-performance asynchronous drivers (asyncpg) and mature tooling for profiling complex queries.

#### DECISION
Selected RDBMS: PostgreSQL

#### TRADE-OFFS & LIMITATIONS
- Connection Overhead: unlike MySQL (Thread-per-connection), for example, Postgres creates a separate OS process for each connection (Process-per-connection) — expensive in terms of memory;
- VACUUM & MVCC: requires monitoring `autovacuum` processes to prevent table bloat under high write/delete loads;
- Configuration complexity: by default, very conservative settings are set (shared_buffers, work_mem, etc.), which must be optimized manually.

#### RATIONALE & ALTERNATIVES CONSIDERED
Options considered (Licensing):
- MySQL (Open-source with commercial elements);
- MariaDB (Open-source with commercial elements);
- PostgreSQL (True Open Source);
- SQLite (True Open Source).

Rejected options:
- SQLite;
- MySQL;
- MariaDB.

Primary reasons:
None of the alternative DBMS provide the necessary flexibility and completeness of the requirements embedded in the schema (specifically: complex functional indexes, Window Functions, and strict data typing), while remaining a fully Open Source solution.

#### Theory

<details>

> **Self-Note:** *SQLite*
> - Difficulty in horizontal scaling;
> - Lack of built-in access control (RBAC at the DB level);
> - Constraints during concurrent writing (locking the entire database during write operations).
>
> **Note (Testing):** SQLite is acceptable for use in tests, however, this entails risks of discrepancy in Database Constraints consistency between test and production environments.

> **Self-Note:** *PostgreSQL*
> - Full ACID compliance;
> - ENUM in PostgreSQL is a separate type (stored as a 4-byte integer); *easy to add, but difficult to delete/rename*;
> - PostgreSQL v18 introduced support for UUID v7; *advanced-alchemy allows using UUID v7*;
> - Support for partial indexes;
> - Good support for asynchrony; *asyncpg is one of the fastest drivers in the Python stack*;
> - Powerful Window Functions;
> - Native expression indexing; *in PostgreSQL, Functional Indexes and Expression Indexes are used as synonyms*;
> - Allows storing data in JSONB format;
> - CHECK — a full-fledged data validator at the kernel level.
>
> It should also be noted that PostgreSQL is a kind of "Enterprise for the poor," a full-fledged extensible platform for data management with a powerful scheduler.

> **Self-Note:** *MySQL & MariaDB*
> - Limited indexing: Less flexible work with functional indexes; lack of native support for GIN indexes, making search by nested JSON structures inefficient.
> - Looser Typing: Specific implementation of `ENUM` and handling of `Timezones` requires additional efforts at the application level to maintain data consistency.
> - Analytical ceiling: Historically weaker optimization of complex analytical queries (`Window Functions`, `Recursive CTE`) compared to the PostgreSQL engine.
> - Licensing risks: Issues of ownership and licensing (Oracle/MariaDB Corp) make PostgreSQL a safer "True Open Source" choice for long-term projects.

</details>

---

## Connection Pooler Selection

#### CONTEXT
- Client-side pooling (inside SQLAlchemy/asyncpg) limits scaling:
    - Geometric progression of connections:
        - Essence: Each application worker creates its own independent pool;
        - Consequences: If each worker has its own pool (e.g., `min_size=10`), then launching 10 workers immediately and permanently reserves 100 connections in Postgres, even if the application is idle.
    - Inflexible distribution:
        - Essence: Isolation of pools at the OS process level (workers);
        - Consequence: Worker #1's internal pool cannot "give" its free connections to worker #2, which is currently under heavy load. Connections are "locked" inside the application processes.

#### DECISION
Selected Connection Pooler: PgBouncer  
Configuration:
- Pool Mode: transaction  

#### TRADE-OFFS & LIMITATIONS
- Transaction Pooling Constraints:
    - Disallows session-level features like temporary tables or `SET` commands, requiring adaptations like using `SET LOCAL`.
    - Unpredictability of session-level locks;
    - Additional driver configuration required (`statement_cache_size=0`) to avoid "statement not found" errors.
- Single-threaded (can be a problem for massive Enterprise systems);
- Debugging: may "swallow" or alter specific Postgres errors, issuing a generic connection error instead;
- Additional node in the infrastructure, requiring separate monitoring and limit configuration.

#### RATIONALE & ALTERNATIVES CONSIDERED
Options considered:
- Multi-threaded Odyssey (Yandex);
- Pgpool-II "Combine" (Connection Pooling, Load Balancing);
- Lightweight single-threaded PgBouncer.

Rejected options:
- Odyssey;
- Pgpool-II.

Primary reasons:
- For most tasks, including my project, the PgBouncer + PostgreSQL combination is more than enough;
- Odyssey and Pgpool-II are more difficult to configure, especially Pgpool-II;
- PgBouncer is the most lightweight (compared to Odyssey/Pgpool-II), which is relevant for my hardware (AMD FX-8320 / 12 GB RAM).

#### Theory

<details>

> **Self-Note:** *Why do we need a pooler?*
> 
> Unlike MySQL, for example, which spawns lightweight threads, Postgres performs a fork of the main process (`postmaster`) for every new incoming connection.
> Therefore, we limit max_connections (default=100), and if the 101st client arrives, they receive "FATAL: sorry, too many clients already."
> This provides isolation (if one process crashes, it doesn't take down the entire database), but as we know, creating/killing a process is expensive.
>
> The "heavy fork" problem on the DB server side can be solved at the application level, for example, via asyncpg (asyncpg.create_pool()) or sqlalchemy (pool_size and taking connections from QueuePool), but it is also important to consider that this only works in Session Pooling mode. Thus, we will hold active connections. However, we encounter another problem — scaling and the increase in the number of connections.
> **What I mean:** if we run uvicorn, for example, and as a rule we use n workers, then each worker is a separate process with its own instance of sqlalchemy and connection pool. That is, pool_size=20 * n active connections to Postgres + python code overhead (queue management, pre-ping checks, cleaning old connects).
>
> Conclusion:  
> Using a pooler inside the application creates a rigid dependency of DB resources on the number of backend workers. At the infrastructure level, this deprives us of flexibility during scaling. Implementing an external pooler allows us to break this link, turning connections into a common, effectively managed resource.

> **Self-Note:** *3 pooler modes*
> 
> - session pooling - the connection is assigned to the client until they disconnect (session.close());
> - transaction pooling - the connection is given to the client only for the duration of the transaction;
> - statement pooling - the connection is given for each individual SQL query.
> - **Note:** 
>   - session pooling - the safest but least efficient mode for scaling, as it doesn't provide transaction "compression";      
>   - transaction pooling - allows for effective multiplexing of thousands of requests through a small pool of DB processes;    
>   - statement pooling - transactions (BEGIN...COMMIT) break in this mode because different lines of the same transaction might go to different Postgres processes.    

> **Self-Note:** *Transaction Pool Mode*
> 
>  From the perspective of overall system throughput, `pool_mode=transaction` is the most performant; from the perspective of a single query, it may be slightly slower than session pooling with an enabled statement cache.
> 
> **The Problem:** 
> *Incompatibility of Prepared Statements and Transaction Pooling*
> 
> `asyncpg` (and sqlalchemy under it) caches statements on the client side (in the Python process memory) and by default prepares a query (PREPARE stmt AS...) and attempts to execute it by name. In pool_mode = transaction, the next command may land on a different Postgres process that knows nothing about this stmt. This is why a certain complexity arises in configuring the sqlalchemy engine connection in transaction mode.  
> 
> **The Solution:**
> *In sqlalchemy settings, we set:*
> - statement_cache_size=0 - disable the prepared statement cache;   
> - poolclass=NullPool - every DB call from the application will initiate a new TCP/Unix connection to PgBouncer. 
> - **Note:**       
>   - statement_cache_size=0 - a slight performance loss, as every query is parsed by the database again.

> **Self-Note:** *To summarize the problems PgBouncer solves*
> 
> - Protection against "protocol shock":  
> FastAPI + asyncpg can generate hundreds of concurrent requests per second. Even if there is only one service, it runs in an event loop. Without a pooler, every new connection is a heavy OS process fork on the Postgres side.
>
> - Scaling:  
> Easy to add new instances (either via Docker or via workers). Without a pooler, alchemy might hold open connections; we solve the "heavy fork" problem on the DB server side, but another problem arises: when adding an instance, the number of connections to Postgres grows, which leads to context switching during peak loads.
> 
> - Infrastructural purity:  
>   - Allows, for example, for database maintenance (there are pooler pause commands), meaning pgbouncer pauses the connection while the connection to the DB is not dropped;
>   - Allows for strictly limiting the resources the application can consume from the DB server.
>
> **Note:**
> Easy to add new instances (either via Docker) - by "via Docker," I mean that Docker containers connect to a single PgBouncer (centralized pooler).

</details>

---

## ORM Selection

#### CONTEXT
ORM Selection Criteria (Derived from Database Schema Blueprint | PostgreSQL):
- Structural Criteria:
  - Full support for advanced SQL features (Window Functions, CTEs) for workout analytics;
  - Granular control over relationship loading (avoiding N+1) and complex joins/aggregations;
  - Complex PostgreSQL constraints, complex indexes (functional/partial).
- Maintainability & Data Integrity Criteria:
  - Support the Data Mapper pattern to decouple business logic from data persistence (reducing cognitive load, enhancing testability and modularity);
  - Ability to implement data copying logic (snapshots) between templates and session history at the ORM level (via event/hook mechanisms).

#### DECISION
Selected ORM: Advanced Alchemy

#### TRADE-OFFS & LIMITATIONS
- Advanced-Alchemy:
  - Requires studying the documentation;
  - The project is relatively young; major updates may contain breaking changes requiring refactoring;
  - In some cases, abstractions become redundant, and one must use SQLAlchemy directly to implement complex/specific logic;
  - Integration with FastAPI:
    - Built-in filtering/sorting mechanisms may require additional manual handling, as they allow passing incorrect parameters (e.g., non-existent columns) to the DB, leading to exceptions.

- SQLAlchemy:
  - Fairly high entry barrier;
  - ORM layer "magic" and superficial knowledge of the library itself lead to the N+1 problem, non-optimal queries, etc.;
  - Overhead in the form of an ORM layer on one hand, and development convenience on the other.

#### RATIONALE & ALTERNATIVES CONSIDERED

Options considered:
- Tortoise ORM (Active Record);
- SQLModel (Data Mapper);
- SQLAlchemy 2.0+ (Data Mapper (fundamental), Active Record (can be imitated via DeclarativeBase));
- Advanced Alchemy (Service/Repository).

Rejected options:
- Tortoise ORM;
- SQLModel.

Primary reasons:    
- Both libraries are good for rapid prototyping, for applications with simple business logic and high scalability requirements, where deep control over JOINs/aggregations is not needed and there are no high requirements for analytics (Window Functions, CTE).

**Note:** The combination of requirements for analytical flexibility and strict data isolation effectively makes SQLAlchemy the only mature choice in the Python ecosystem capable of meeting all selection criteria without degrading the architecture to the Raw SQL level.

The selection of Advanced Alchemy is driven by:
- Scalability: To maintain the codebase at an acceptable level (decoupling, cognitive load), it is necessary to either implement the Repository/DAO pattern independently or use ready-made solutions;
- Routine automation: Eliminates the writing of boilerplate code for CRUD operations;
- Implementation complexity: The Service/Repository layer in projects with complex business logic requires deep knowledge of SQLAlchemy's internal workings;
- Risk reduction: Using advanced-alchemy allows for minimizing the risk of typical design errors (session lifecycle management, N+1 optimization, Identity Map consistency).

#### Theory

<details>

> **Self-Note:** *Tortoise ORM & SQLModel*
> - Tortoise ORM — an implementation of the Active Record pattern, where the model (class) is the database table itself, and an instance of the class is a row in that table. This means business logic and data handling logic (saving, deleting, searching) are mixed in one place. The code is concise, but in complex systems, it often leads to models becoming "too fat" and difficult to maintain.
>
> - SQLModel (Data Mapper) — essentially a wrapper over SQLAlchemy with typing and Pydantic attached; the main problem is tight coupling: it forces the same model to be both a Pydantic schema and a SQLAlchemy table, violating the Single Responsibility Principle by mixing data transfer (DTO) and data access (DAO) concerns.
> The essence of the Data Mapper pattern: models are simply data descriptions (can be "pure" classes), and an external intermediary — the Session (Unit of Work) — is responsible for working with the database. The user object knows nothing about the database. To save it, it must be passed to the session: `session.add(user)`.  

> **Self-Note:** *SQLAlchemy Features*
> - De facto golden standard in large projects;  
> - Powerful, mature, and flexible library with detailed high-quality documentation;  
> - Divided into:  
>   - SQLAlchemy Core: powerful SQL query builder. Working with tables and columns directly. This is "low level," as close as possible to raw SQL;
>   - SQLAlchemy ORM: an add-on that implements Data Mapper;
> - With knowledge of SQL syntax, queries are built like a constructor;
> - Allows building complex joins and applying window functions.

</details>

---

## Web Layer Selection

#### CONTEXT
- Core Capabilities:
  - Integration with SQLAlchemy;
  - Asynchrony.
- Developer Experience:
  - Automatic documentation generation;
  - Typing.
- Efficiency & Maintenance:
  - Performance and resource consumption by the framework itself;
  - Support for validation and serialization (or a relatively "cheap" implementation);
  - Prevalence (Community & Hiring).

#### DECISION
Selected Web Layer: FastAPI

#### TRADE-OFFS & LIMITATIONS
Below are the fundamental features and limitations of the framework:
- Tight coupling with Pydantic: 
  - Input: FastAPI uses Pydantic in its very core for parsing the request body, path parameters, and query parameters;
  - Output: one can use, for example, a custom Response (`msgspec.json.encode`), but the automatic generation of the OpenAPI schema and the overhead of `jsonable_encoder` are lost.
- Minimalism: 
  - Out of the box: no ORM, no built-in migration system, no admin panel, no user management;
  - Ecosystem: there is a large number of libraries, but they are maintained by enthusiasts.
- Overhead and performance:
  - It is "fast" in terms of asynchrony (IO) but "heavy" in terms of CPU (due to a lot of magic under the hood during validation).
- Dependency Injection:
  - Coupling with the framework;
  - DI via function parameters rather than via constructor;
  - Lack of a full-fledged IoC container.
- Background Tasks:
  - Suitable for simple tasks (for more complex ones, something like Taskiq is needed).
- Heavily tied to Swagger generation.

#### RATIONALE & ALTERNATIVES CONSIDERED
Options considered:
- FastAPI;
- Litestar.

Rejected options:
- Litestar.

Primary reasons:  
- Despite excellent performance and a plugin system, Litestar remains a less common solution in the industry (as of April 2026).

The selection of FastAPI is driven by the following factors:
- Compliance with key criteria: fully covers requirements for asynchrony, typing, and integration with the chosen stack (SQLAlchemy).
- Relevance (April 2026): the framework remains the industry standard and the most in-demand solution in the Python stack, ensuring long-term support and an extensive base of ready-made solutions.
- Rejection of "box magic": the absence of built-in authentication and caching mechanisms is a conscious choice. Despite the increase in labor costs (development cost), a custom implementation allows:
  - Thoroughly analyzing security logic (Auth/Authz) and cache invalidation mechanisms;
  - Avoiding the unnecessary overhead of universal solutions;
  - Building the architecture "from first principles," understanding how every node of the system works.

#### Theory

<details>

> **Self-Note:** *Features of DI in FastAPI*
> 
> Synchronous nature of FastAPI DI: to understand this, one should separate the concepts of **declaration method** of a dependency and **its invocation mechanism**.
> - Example one: when using **Depends(your_func)**, FastAPI does the following under the hood:
>    - If your_func is defined as def: FastAPI calls it directly in a separate thread (worker thread) from an external pool (ThreadPool) to avoid blocking the main Event Loop;
>    - If your_func is defined as async def: FastAPI waits for its execution via await.
> 
> - Example two: suppose there is an endpoint -> **async def index(user=Depends(get_user), db=Depends(get_db))**, then:
>    - FastAPI will first fully resolve get_user, and only when it returns a result will it begin resolving get_db. It does not launch them concurrently via asyncio.gather(), even if both are asynchronous;
>    - This is the essence of the synchronous nature; the problem lies in the dependency graph — FastAPI calculates dependencies sequentially rather than in parallel.
> 
> - Lack of dynamic/deferred resolution: 
>    - In classical DI containers (as in Java or some Python libraries), we can obtain a "factory" or "proxy" that will create an object only at the moment of access:
>      - In FastAPI, Depends is an executor: a request arrives -> FastAPI looks at the function signature -> synchronously (sequentially) goes through the dependency tree from bottom to top -> creates all objects -> passes the ready values to the endpoint;
>      - From this, it follows that the endpoint's response time is the **sum of the resolution times of all its dependencies**.
>
> **Note (AMD FX-8320)**: 
>
> The latency accumulation from sequential dependency resolution is particularly noticeable on systems with limited CPU performance. For optimization, independent IO-bound operations are best grouped inside a single dependency and launched in parallel via `asyncio.gather`.

> **Self-Note:** *Lifecycle and Context Manager (yield)*
> 
> Dependencies with yield work as a rigid context manager: code before yield -> endpoint -> code after yield.
>
> This chain is unbreakable and synchronized with the HTTP cycle. One cannot "release" the execution of post-logic (e.g., database commit) to the background without delaying the completion of the HTTP response if it is part of the Depends chain.

> **Self-Note:** *What is an IoC Container?*
> 
> **Concept of IoC (Inversion of Control):**
>  - In normal code, we manage the creation of objects ourselves. For example, if a service needs a repository, we write repo = Repository() inside the service. This is a hard link;
>  - Inversion of Control is when our code doesn't create dependencies, but someone from the outside "gives" them to our code. We simply say, "I need a repository," and the system provides it to us.
> 
> **IoC Container** is a "smart warehouse" or manager of our application's objects. Its tasks:
> - **Registration:** We record rules in it (e.g., "When UserRepository is requested, create an object of the PostgresUserRepository class"); **Essence:** in complex systems, the class we request (interface) and the class that is ultimately created (implementation) are different entities. This allows swapping logic (e.g., for tests) without changing the code in the endpoints themselves;
> - **Lifecycle Management (Scope):** The container decides whether to create a new object for every request or provide the same one (Singleton);
> - **Auto-wiring:** If we ask for a service that needs a repository, and the repository needs a database session, the container will assemble this entire chain itself and give us the finished service.
> 
> **Note:** "FastAPI has no full-fledged IoC container"?
> 
> FastAPI has a built-in `Depends()` system, but technically it is a **Service Locator** working at the level of handler functions (endpoints), not a full container. That's why it's called "incomplete."
> 
> Example: -> **async def get_users(repo: UserRepository = Depends()):** -> here UserRepository is both the "name" of the dependency and the code itself. FastAPI simply creates an instance of this specific class. That is, we ask for class A — an instance of class A is created; there is no intermediate "smart" layer that could flexibly swap the logic of this class throughout the application without changing the code in the endpoints. When experienced developers say that FastAPI's DI is "fake" or "incomplete," they are hitting exactly on the point of the lack of an IoC container.

</details>

---

## In-Memory Storage Selection

#### CONTEXT
- JWT Revocation: blacklisting for refresh tokens is required;
- Auth Entity Caching: storing serialized user objects without expensive requests to the relational DB;
- Rate Limiting (Future Scope);
- Resource List Caching: caching expensive paginated results (e.g., User Lists, Exercise Lists).

**Note (Rate Limiting):** This can be implemented via the `cashews` library (via rate_limit or failover + rate_limit), as it is already present in the stack. This will avoid bloating the number of dependencies with specialized limiters (current requirements do not imply a complex hierarchy of limits).

**Note:** Refresh tokens usually have a long life cycle — the storage must support flushing data to disk; one could dedicate one storage solely for tokens, but that would mean +1 node in the infrastructure and additional load for my hardware (AMD FX-8320). 

**Note:** At the current stage of development, I maintain that all cached objects have a set TTL, including token blacklisting. The most optimal Eviction Strategy would be to set the parameter `maxmemory-policy: volatile-ttl` and increase memory limits.  

#### DECISION
Selected In-Memory Storage: Valkey

Configuration:
- Eviction Strategy: volatile-ttl + Increased Memory Limit

**Note:** For hot data (e.g., UserAuth), `msgspec.msgpack` was chosen as the serializer/deserializer to save CPU and RAM.

#### TRADE-OFFS & LIMITATIONS
- RAM Consumption: storage in RAM is more expensive than on SSD/HDD, requiring the implementation of TTL and data eviction policies;
- Persistence (AOF): the need to enable AOF mode for the preservation of critical data (e.g., blacklisted tokens), which reduces the overall system throughput;
- Durability & Hardware Limits: full guarantee of writing to disk requires calling fsync for every operation, which negates the advantage of an in-memory solution and significantly increases latency;
- Consistency vs. Availability Issue: replication in Redis/Valkey is asynchronous by default; if the master node writes data and immediately "crashes" before it can transfer it to the replica, data loss will occur;
- Network Overhead: relevant if the application and storage are on different nodes (with local placement, optimization via Unix sockets is possible);
- CPU Overhead during serialization/deserialization: a factor, but minimized by using an efficient format like `msgspec` instead of standard `json` or `pickle`.
- Additional node in infrastructure and a "new point of failure": lack of fallback logic implementation in case of storage unavailability can lead to total application failure;
- Data model limitations: lack of the flexibility of relational DBs (complex queries, JOINs, filtering by fields on the storage side are impossible).

#### RATIONALE & ALTERNATIVES CONSIDERED

Options considered:
- Redis
- Valkey
- KeyDB
- Memcached

Rejected options:
- Redis
- KeyDB
- Memcached

Primary reasons:
- Redis - changed its license to Source Available; it can be used in personal projects, on company servers, and even in commercial products, but Redis has ceased to be Open Source in the legal sense (OSI-compliant).
- KeyDB - a Redis fork, fully multi-threaded, Open Source, but more focused on Snapchat's needs (acquired by Snap Inc).
- Memcached - multi-threaded, as simple as possible, easy to set up, but only allows for storing strings (cannot work with data structures) and has no persistence capability, which is critical for refresh token blacklisting.

The selection of Valkey is driven by the following factors:
- Core:
  - Open Source Standard: the project is a direct continuation of the original Redis, backed by major industry players (AWS, Google Cloud, Oracle).
  - Support for the REdis Serialization Protocol (RESP) allows using Valkey with any existing libraries and tools without code changes (the de facto standard for replacing Redis).
- Additional:
  - Performance and innovation: inclusion of multi-threading and optimizations that become part of paid editions in the original Redis.

#### Theory

<details>

> **Self-Note:** In programming, we are used to separating `str` (text) and `bytes` (bytes). But at the database protocol level (Redis/Valkey/Memcached), the term "String" historically means a "sequence of bytes."

> **Self-Note:** *Advantages of Valkey*
> - True Open Source: currently (April 2026), the primary official alternative to the previously free Redis;
> - Full backward compatibility with Redis: Redis commands work in Valkey;
> - Valkey 8.0 implements multi-threaded I/O processing and partial parallelization of command execution (performance gain on multi-core processors);
> - Scalability and clustering: improved performance in cluster mode (per-slot metrics, automatic failover);
> - Memory efficiency: old Redis hash tables replaced with a new structure (Open Addressing + SIMD).
>
> **Note:** 
> - Redis primarily uses a single-threaded architecture for command execution. This creates a risk of "Head-of-line blocking," where a heavy operation completely blocks the processing of other requests.
> - In Valkey, command execution itself can be distributed among threads (in certain scenarios), which fundamentally reduces the risk of a single "heavy" command blocking the entire storage.

> **Self-Note:** *4 Persistence Strategies*
> 
> RDB - enabled by default | set the `save` parameters (RDB works) or disable with `save ""` (RDB off).
> 
> AOF - disabled by default | parameter `appendonly no` (AOF off) or `appendonly yes` (AOF on).
> 
> - **RDB (Valkey Database Backup)** - "snapshots" of all data in memory taken at specific intervals (e.g., every 5 minutes if 100 keys changed).
>    - Pro: Very compact files and fast loading upon start.
>    - Con: If Valkey crashes between snapshots, data from the last few minutes is lost.
>
> - **AOF (Append Only File)** - Valkey records every write operation to a log file in real-time.
>    - Pro: Maximum data integrity (nearly zero risk of loss).
>    - Con: Additional write load is created as the log file grows constantly (can reach gigabytes), and at a certain point, a rewrite will trigger, which may lead to brief CPU and disk load.
>
> - **RDB + AOF** - AOF for reliability upon restart, and RDB for fast backups and transferring data to replicas.
>
> - **No Persistence** - write to disk is completely disabled. Valkey becomes a pure RAM cache. All data disappears upon restart.

> **Self-Note:** *Configuration for AOF parameter `appendfsync`*
> - **appendfsync always (synchronous):** Calls fsync after every write command; maximum reliability, but catastrophic drop in performance.
> - **appendfsync everysec (default, asynchronous):** Calls fsync once per second; fairly high speed, disk write occurs in batches.
> - **appendfsync no:** The system fsync function is not called by Redis/Valkey; managed by the OS, maximum speed.
>  
> **Note:** Unlike PostgreSQL, which by default (parameter `synchronous_commit=on`) guarantees Strict Durability through synchronous writing to the WAL, Valkey (even with AOF enabled) is usually configured for asynchronous flushing (`appendfsync everysec`).

</details>

---

## Reverse Proxy Selection

#### CONTEXT
What issues may we encounter if we expose only a "naked" application server:
- SSL/TLS Termination:
  - Essence: Traffic encryption and decryption is a resource-intensive task.
  - Consequences: The backend application spends resources on heavy cryptography instead of business logic, which can create excessive CPU load and increase latency when processing new connections.
- Scaling:
  - Essence: Without an external balancer, the application is tied to a specific network port on a single host.
  - Consequences: 
    - Vertical growth limitation: We can only scale within a single node (by increasing the number of workers), which is limited by the current CPU's power.
    - Lack of a built-in mechanism for load balancing traffic between multiple application instances: We cannot run multiple copies (instances) of the application behind a common IP address.
    - Single Point of Failure: If the application server process hangs or crashes, the entire service becomes unavailable as there is no way to instantly switch traffic to another working instance.
- Connection Termination & Request Buffering:
  - Essence: Client connections (especially mobile) are often unstable or slow (slow client / slowloris-like behavior).
  - Consequences: Inefficient use of worker resources. Granian/Uvicorn are forced to hold open connections with slow clients while waiting for the request body to be transmitted. This can lead to irrational retention of worker resources and a decrease in total system throughput.
- Security:
  - Essence: Direct exposure to malicious traffic (L7 DDoS, vulnerability scanning, bots).
  - Consequences: Lack of a first line of defense. Implementing Rate Limiting and traffic filtering at the application level leads to non-target consumption of worker resources. Without a proxy server, malicious requests reach the application code, increasing the likelihood of backend degradation under abnormal or malicious traffic.
- Health Checks & Availability:
  - Essence: The need for real-time monitoring of service health.
  - Consequences: In the event of a hang or crash of one of the workers, there is no mechanism to automatically exclude unhealthy nodes from rotation, leading to a rise in 5xx errors.
- Traffic Compression:
  - Essence: Configuring compression for heavy JSON responses at the application level (FastAPI - GZipMiddleware). 
  - Consequences: Performing compression inside the application creates additional CPU load, which can reduce backend throughput when transmitting large amounts of data.
- CORS:
  - Essence: Configuring CORS at the application level.
  - Consequences: Additional Middleware; no way to terminate "preflight" (OPTIONS) requests before they reach the application, resulting in unnecessary overhead logic at the backend level.

**Note (AMD FX-8320):** On the `Piledriver` architecture, TLS and compression tasks create high resource contention within shared compute modules. Offloading these operations to the proxy level reduces the load on the application's CPU workers, neutralizing the risk of latency spikes, which are particularly critical given the low single-core performance.

#### DECISION
Selected Reverse Proxy: Angie

Configuration:
- Infrastructure: Delegation of SSL termination, traffic compression, and passive Health Checks to the reverse proxy level.
- Network: Interaction with the application server (Granian) via UDS.
- Security: Configuration of CORS and primary request limits (Rate Limiting) on the reverse proxy side.

**Note (Rate Limiting Strategy):** A multi-level defense was chosen: basic IP-based limiting at the proxy level to protect infrastructure, and granular application-level limiting to control business resources (Future Scope).

**Note:** Active Health Checks are only available in Angie PRO.

#### TRADE-OFFS & LIMITATIONS
- Infrastructural complexity: An additional node in the system, complicating deployment and monitoring processes.
- Configuration duplication and desync: Risk of desynchronization of settings (CORS, limits, timeouts) between the application code and the reverse proxy configuration.
- Complex syntax: Unlike Caddy or Traefik, NGINX/Angie configuration is low-level and requires an understanding of how directives work.
- UDS limitations: Loss of network mobility (requires switching to TCP when distributing across different nodes), lack of direct debugging via curl to a port, and the need to configure access rights and Shared Volumes for the socket file.
- Limited visibility: The application does not see requests blocked at the proxy layer (rate limiting, CORS).
- Complication of the SSL lifecycle: The need to integrate and maintain third-party utilities (mkcert, Certbot) for certificate lifecycle management, whereas in Caddy and Traefik, this process is fully automated.
- Entry point centralization (Single Point of Failure): Proxy configuration errors or incorrect reloads can affect all incoming traffic (application unavailability).

#### RATIONALE & ALTERNATIVES CONSIDERED

Options considered:
- Caddy
- Traefik
- NGINX
- Angie

Rejected options:
- Caddy
- Traefik
- NGINX

Primary reasons:
- Traefik: Automatic SSL, high performance, Auto-discovery of services, but historically tailored for network interaction (TCP/HTTP), making UDS configuration specific, complex, and lacking flexibility.
- Caddy: Full SSL automation, maximally simple and concise config, excellent performance for most tasks, but many low-level parameters (buffering, timings, fine TCP/UDS tuning) are hidden or hard-coded "under the hood."

NGINX(OSS) vs Angie(OSS):
- Interactive Dashboard:
  - Vanilla NGINX lacks visualization and detailed statistics.
  - Angie features a web interface with statistics on traffic, upstreams, and errors.
- Metrics Export to JSON and Prometheus:
  - Angie can provide detailed statistics in JSON format via API and directly in Prometheus format; no need to install a separate nginx-exporter.
- Dynamic Upstream Reconfiguration:
  - In NGINX, to add a new server to the balancer, you must edit the config and perform a reload.
  - In Angie, you can change the upstream composition (add/remove servers) and parameters (temporarily change server "weight") via API without restarting the main process.
- HTTP/3 Support:
  - In NGINX, this was in experimental mode for a long time or required complex builds with specific libraries.
  - In Angie, it is native "out of the box" using standard system libraries (OpenSSL 3+).
- Improved Passive Health Checks:
  - Unlike NGINX, Angie not only allows removing problematic backends from rotation but also visualizes their status on an interactive dashboard.

The selection of Angie is driven by the following factors:
- Primary:
   - The necessity of working via UDS: Traefik and Caddy support UDS in a limited or less flexible manner, while Angie provides full control over low-level configuration.
   - Requirement for fine-grained control over network behavior (buffering, timeouts, keepalive, backpressure): solutions with "high-level abstraction" hide or limit these settings, making it difficult to optimize data transfer between the proxy and backend.
   - Built-in observability (Prometheus format metrics, JSON API) without the need for additional components.
- Secondary:
   - Native HTTP/3 support, requiring no custom builds or unstable dependencies.

#### Theory

<details>

> **Self-Note:** *Role of the proxy server and application server*
>
> **Proxy** — accepts bytes from the internet, performs SSL decryption, and passes them on.
> 
> **Application Server (Granian/Uvicorn)** — accepts these bytes from the proxy, converts them into a Python `scope` dictionary, and "feeds" them to the application (FastAPI). The application looks at the `scope`, identifies which router to call, and executes the business logic.
>
> The essence of ASGI/WSGI, simplified: we choose a specific "adapter" (application server) that supports the protocol we need (ASGI/WSGI) to "bridge" the network and our synchronous/asynchronous code.
> - WSGI: One request — one thread. If a request is long (e.g., waiting for a DB response), the thread is occupied and cannot take on other tasks.
> - ASGI: Allows the server to process thousands of connections in a single thread. While one request waits for data from disk or the database (IO-bound), the Event Loop switches to processing another request.

> **Self-Note:** *SSL/TLS Termination (encryption) vs Connection Termination (TCP sessions)*
> 
> SSL/TLS Termination:
> - The client communicates with the proxy via an encrypted channel (HTTPS). The proxy decrypts the packets and passes them to Granian/FastAPI in "clear" form (HTTP) via Unix socket/TCP.
> 
> Connection Termination (TCP sessions):
> - The proxy acts as a session "separator." It supports thousands of open connections with user browsers (which may hang for a long time without sending anything) while maintaining only a few very fast and efficient connections to the backend. **Why?:** Creating a new TCP connection involves overhead (handshake). The proxy takes on the burden of "holding" lazy clients and only loads the backend when a request is truly ready.

> **Self-Note:** *Keep-Alive (Persistent Connection)*
> 
> Keep-Alive is a mechanism that allows using the same TCP connection to send multiple HTTP requests and receive responses without tearing down the connection each time.
> How it works: After the first request, the connection is not broken but remains "open" in standby mode. The next request will go through the same "channel" instantly.

> **Self-Note:** *Proxy <-> App Interaction: TCP vs UDS*
>
> When deployed locally (on the same server), the choice of communication protocol between the proxy and backend (Granian/Uvicorn) critically affects performance.
> 
> Important clarification: The Linux kernel does not care whether it is a real network interface card (NIC) or a virtual "loopback" interface.
> 
> - **TCP (127.0.0.1:8000):** Data passes through the kernel's full network stack. Even on a local host (loopback), this includes:
>    - Encapsulation of data into TCP packets.
>    - Calculation of checksums for each segment.
>    - Traversal through the loopback interface.
>    - Decapsulation on the receiver side.
> - **UDS (/tmp/app.sock):** Data is transmitted as a direct stream of bytes between processes via a buffer in the kernel.
>     - Direct copying: The kernel simply moves data from the memory of one process to the memory of another.
>     - Speed: Significantly faster than TCP due to the absence of checks and packet wrapping.
> 
> **Establishing Connections (Handshakes & Ports)**
> - **TCP:**
>    - Procedure: Each new connection requires a "handshake" (**SYN -> SYN-ACK -> ACK**) unless Keep-Alive is used.
>    - Risk (Port Exhaustion): Under high load (thousands of requests per second), the system may exhaust the limit of ephemeral ports (Ephemeral Port Exhaustion), leading to refusal of new connections.
> - **UDS:**
>    - Mechanics: A connection is established by simply opening the socket file. No ports means no limits on them.
>    - Security: Access to the socket can be restricted by file system permissions (e.g., only for the `nginx` and `alexander` users).

</details>

---