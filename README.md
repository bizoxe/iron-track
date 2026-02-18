<div align="center">
  <a href="https://github.com/bizoxe/iron-track">
    <img src="docs/_static/logo.svg" width="350" alt="IronTrack Logo">
  </a>

  <h3>Experimental async backend sandbox built for performance and architectural testing</h3>
  <p>Focused on concurrency patterns, database optimization, and constraint-driven experiments within a workout tracking domain.</p>
</div>

---

[![CI Status](https://github.com/bizoxe/iron-track/actions/workflows/ci.yaml/badge.svg)](https://github.com/bizoxe/iron-track/actions/workflows/ci.yaml)
[![Coverage Status](https://img.shields.io/codecov/c/github/bizoxe/iron-track?logo=codecov&logoColor=white)](https://codecov.io/gh/bizoxe/iron-track)
[![Release Status](https://github.com/bizoxe/iron-track/actions/workflows/release.yaml/badge.svg)](https://github.com/bizoxe/iron-track/actions/workflows/release.yaml)
[![Docs](https://img.shields.io/badge/docs-view%20now-blue.svg?style=flat&logo=sphinx&logoColor=white)](https://bizoxe.github.io/iron-track/)

[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776ab?logo=python&logoColor=white)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-4bc51d?logo=opensourceinitiative&logoColor=white)](https://opensource.org/licenses/MIT)

---

## 🎯 Why

IronTrack is an architectural sandbox built around a realistic domain model.

> [!NOTE]
> The project is intentionally benchmarked on constrained hardware (**AMD FX-8320 | HDD**) to evaluate architectural behavior and stability beyond "cloud-ideal" conditions.
> 
> Testing under high I/O latency and CPU contention highlights bottlenecks that are typically masked by modern high-performance infrastructure.

> [!IMPORTANT]
> This is a **learning and exploration project**, not a production-driven business application.
> 
> Advanced optimizations (such as PgBouncer tuning, custom logging, or granular connection pooling) are implemented to study system behavior under stress. While these might be considered "over-engineering" for a standard functional requirement, here they serve as the core subjects of architectural research and performance analysis.

The project focuses on:

- Working under hardware constraints instead of assuming over-provisioned cloud resources.
- Understanding where latency actually comes from (serialization, CPU-bound tasks, I/O).
- Prioritizing empirical measurements over assumptions when making architectural choices.
- Documenting trade-offs through ADR to keep reasoning explicit.

The workout tracking domain provides enough complexity to model real interactions 
(auth, permissions, relational data) without the overhead of artificial complexity.

---

**Inspiration & Standards**  
The project conventions, structure, and DX workflows are inspired by the **litestar-org** ecosystem.   
I have manually adapted these patterns to the FastAPI environment to practice modular architecture and keep the system predictable as its complexity grows.  
The goal is not to replicate the ecosystem, but to analyze and apply the underlying architectural reasoning within a FastAPI-based stack.

<details>
<summary><b>What's Inside for You</b></summary>
 
Below is a brief list of implementations that may be useful to the community as examples of solving specific technical tasks.

**Important:** These implementations do not claim to be universally optimal for every use case. They represent my personal experience in solving tasks within this specific stack and are intended to serve as a starting point for your own projects.

#### Security & Auth

* **Scenario:** Event Loop blocking during password hashing.  
**Approach:** Offloading CPU-bound Argon2 hashing to a dedicated `ThreadPoolExecutor`.  
**Code:** [src/app/lib/crypt.py](src/app/lib/crypt.py)
* **Scenario:** Standardizing JWT signatures.  
**Approach:** Implementing Ed25519 (EdDSA) signatures.    
**Code:** [src/app/lib/jwt_utils.py](src/app/lib/jwt_utils.py)  
* **Scenario:** Lack of native support for HTTP-only Cookie authorization in standard Swagger UI (OpenAPI) docs.  
**Approach:** Custom `JWTCookieSecurity` implementation inheriting from `SecurityBase` that correctly propagates cookie metadata to the OpenAPI schema.  
**Code:** [src/app/lib/auth.py](src/app/lib/auth.py)  
* **Scenario:** Lack of instant JWT-refresh token revocation.  
**Approach:** **JTI Blacklisting** mechanism integrated with Redis/Valkey.  
**Code:** [src/app/domain/users/auth.py](src/app/domain/users/auth.py) and [src/app/domain/users/jwt_helpers.py](src/app/domain/users/jwt_helpers.py)

#### Performance

* **Scenario:** Network stack overhead during inter-container traffic.  
**Approach:** Orchestration via Unix Domain Sockets (UDS) to bypass the TCP stack overhead in inter-container communication.      
**Code:** [docker-compose.yaml](docker-compose.yaml)  
* **Scenario:** JSON serialization bottlenecks in high-load endpoints.  
**Approach:** Response layer based on `msgspec` to reduce serialization overhead with automatic **CamelCase** conversion for frontend compatibility.  
**Code:** [src/app/lib/json_response.py](src/app/lib/json_response.py) and [src/app/lib/schema.py](src/app/lib/schema.py)  

#### Database & Caching

* **Scenario:** SQLAlchemy conflicts with PgBouncer in `Transaction Pooling` mode (prepared statements).  
**Approach:** Fine-tuned Engine configuration (`compiled_cache=None`, `statement_cache_size=0`) for full bouncer compatibility.  
**Code:** [src/app/config/base.py](src/app/config/base.py)  
* **Scenario:** Excessive DB load from redundant permission checks in every request.  
**Approach:** Granular caching of `UserAuth` entities in Valkey with automated invalidation.  
**Code:** [src/app/domain/users/auth.py](src/app/domain/users/auth.py) and [src/app/lib/invalidate_cache.py](src/app/lib/invalidate_cache.py)     
* **Scenario:** Password synchronization between PostgreSQL and PgBouncer.    
**Approach:** Makefile script for automated `userlist.txt` generation directly from PostgreSQL system tables.  
**Code:** [Makefile](Makefile) 

#### Observability & Monitoring

* **Scenario:** Impact of heavy I/O logging on the application's main event loop.  
**Approach:** Non-blocking logging pipeline using `QueueHandler` to offload log writing to a background thread.  
**Code:** [src/app/utils/log_utils/setup.py](src/app/utils/log_utils/setup.py) and [src/app/utils/log_utils/handlers.py](src/app/utils/log_utils/handlers.py)     
* **Scenario:** Difficulties in debugging distributed requests and linking logs across different layers.  
**Approach:** Request correlation via `Correlation ID` (Middleware -> Service -> Repository -> DB).  
**Code:** [src/app/utils/log_utils/middleware.py](src/app/utils/log_utils/middleware.py)  

#### Developer Experience (DX)

* **Scenario:** Database pollution after tests and slow CI pipelines.  
**Approach:** **Transactional Pytest** pattern (automatic transaction rollback after each test).  
**Code:** [tests/integration/conftest.py](tests/integration/conftest.py)  
* **Scenario:** Management overhead of multiple commands for server, migrations, and DB ops.  
**Approach:** Unified CLI interface built with `Typer`, consolidating server commands, `advanced-alchemy` tools, and custom scripts.  
**Code:** [src/app/main.py](src/app/main.py) and [src/app/utils/server_cli.py](src/app/utils/server_cli.py)  
* **Scenario:** Documentation noise from internal ORM fields and unreadable `Annotated` type signatures.  
**Approach:** Custom Sphinx hooks for automated signature cleaning and SQLAlchemy internal attribute filtering.  
**Code:** [docs/conf.py](docs/conf.py)  

</details>

---

## 🛠 Tech Stack

| Category              | Technology                                                                                                                                              |
|:----------------------|:--------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Web Server**        | [Angie](https://en.angie.software/angie/docs/) & [Granian](https://github.com/emmett-framework/granian)                                                 |
| **Language**          | [Python 3.12+](https://www.python.org/) (Typed, Async)                                                                                                  |
| **Framework**         | [FastAPI](https://fastapi.tiangolo.com/)                                                                                                                |
| **ORM & Repository**  | [Advanced Alchemy](https://advanced-alchemy.litestar.dev/latest/)                                                                                       |
| **Database**          | [PostgreSQL](https://www.postgresql.org/)                                                                                                               |
| **Connection Pooler** | [PgBouncer](https://www.pgbouncer.org/)                                                                                                                 |
| **Migrations**        | [Alembic](https://alembic.sqlalchemy.org/)                                                                                                              |
| **Caching**           | [Valkey](https://valkey.io/docs/) (Redis-compatible)                                                                                                    |
| **Logging**           | [structlog](https://www.structlog.org/)                                                                                                                 |
| **Package Manager**   | [uv](https://github.com/astral-sh/uv)                                                                                                                   |
| **Configuration**     | Native Python Dataclasses                                                                                                                               |
| **Documentation**     | [Sphinx](https://www.sphinx-doc.org/) (with [Shibuya](https://shibuya.lepture.com/) theme)                                                              |
| **Quality Control**   | [Ruff](https://github.com/astral-sh/ruff), [Mypy](https://github.com/python/mypy), [Pre-commit](https://pre-commit.com/), [Pytest](https://pytest.org/) |

---

## 🚀 Quick Start

Ensure you have **Docker**, **Make**, and **uv** installed.

### 1. Clone the Repository
```bash
git clone https://github.com/bizoxe/iron-track.git
cd iron-track
```

### 2. Environment Configuration
Install dependencies and set up your local configuration files:
```bash
# Install dependencies via uv
make install

# Copy the development environment template
cp .env.local.template src/app/config/.env
```

### 3. Security Setup (JWT Keys)
The application uses the **Ed25519** algorithm (EdDSA) for secure token signing. This requires a **JWK (JSON Web Key)** stored in your environment configuration.

* **Generate the Key**: Create a new secure key pair using the Makefile shortcut:
```bash
make gen-key
```

* **Setup**:
  * **Copy** the output from the command above.
  * **Open** your `src/app/config/.env` file.
  * **Assign** the value to `JWT_PRIVATE_KEY` using single quotes to avoid shell parsing issues:
```bash
# src/app/config/.env
JWT_PRIVATE_KEY='{"crv": "Ed25519", "x": "...", "d": "...", "kty": "OKP"}'
```

> [!NOTE]
> A single Ed25519 JWK contains both the private and public components required for the EdDSA flow.

### 4. Infrastructure & Data
```bash
# Start PostgreSQL and Valkey
make infra-up

# Initialize Database & Permissions
app database upgrade
app users create-roles
make seed
```

> [!IMPORTANT]
> **Creating roles is mandatory**. You must execute app users create-roles before registering any users, as it initializes the base permission system.

> [!NOTE]
> **Seeding**: The `make seed` command and the Exercise Catalog models are currently in development and not included in this release.

### 5. Run Server
```bash
app server dev
```

> [!TIP]
> Once started, the API will be available at http://127.0.0.1:8000.
>
> Explore the interactive docs at http://127.0.0.1:8000/docs.

---

## 📈 Performance & Scalability

The project includes performance experiments and concurrency analysis. Detailed metrics, hardware specifications, and reproduction commands are documented in the [Performance & Benchmarks](./benchmarks/BENCHMARKS.md) directory.

---

## 📂 Project Structure

```text
├── src/app/       # Application core and business logic.
├── dev/adr/       # Architecture Decision Records (design rationale and history).
├── deploy/        # Infrastructure and deployment setup (PostgreSQL, Angie, etc.).
├── benchmarks/    # Performance testing suite, load scripts, and results.
├── docs/          # Sphinx documentation source files.
└── tests/         # Unit and integration tests.
```

---

## 📚 Documentation

Quick Access:

| Document                                                                           | Description                               |
|:-----------------------------------------------------------------------------------|:------------------------------------------|
| [Installation Guide](https://bizoxe.github.io/iron-track/usage/installation.html)  | Step-by-step first-time setup.            |
| [Development Workflow](https://bizoxe.github.io/iron-track/usage/development.html) | Hot-reload, Docker volumes, and Makefile. |
| [CLI Reference](https://bizoxe.github.io/iron-track/usage/cli-guide.html)          | Application management commands.          |
| [Changelog](https://bizoxe.github.io/iron-track/changelog.html)                    | Full history of project changes.          |

---

## 🔧 Usage & CLI

Below are the most frequently used commands for managing the project.

<details>
<summary>⚙️ <b>Makefile Commands (Automation)</b></summary>

### Infrastructure & DB
* `make infra-up` — Start PostgreSQL and Valkey in Docker.
* `make infra-down` — Stop and remove infrastructure containers.
* `make seed` — Populate the database with initial data.
* `make pgbouncer-sync` — Synchronize PostgreSQL roles with PgBouncer.

### Development & Quality
* `make fix` — Auto-fix linting issues and format code (**Ruff**).
* `make lint` — Run all quality checks (**pre-commit**, **Mypy**).
* `make test` — Execute the test suite with **pytest**.
* `make install` — Refresh environment and install dependencies via **uv**.

</details>

<details>
<summary>💻 <b>Application Commands (App CLI)</b></summary>

### Server Management
* `app server dev` — Start the FastAPI server with **hot-reload** enabled.
* `app server run` — Start the server in production mode.

### Database & Users
* `app database upgrade` — Apply migrations to the latest version.
* `app users create-roles` — Initialize mandatory system roles.

</details>

> [!TIP]
> Use `app -h` to explore the built-in CLI for advanced database and user management.

---

**Contributing**

Contributions are welcome! See the [Contributing Guide](CONTRIBUTING.rst).

**License**

Licensed under the [MIT License](LICENSE).