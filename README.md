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

## 📐 Database Blueprint

<details>
<summary><b>View Database Schema</b></summary>

<br>

#### Schema Version: v0.1 | Last Updated: 2026-04 | Status: Draft | Author: Alexander  
#### STATUS: [x] implemented | [~] partial | [ ] planned  
#### NOTATION: PK: PRIMARY KEY | UUIDv7: UUID version 7 | FK: FOREIGN KEY | UK: UNIQUE | NN: NOT NULL | RULE: Business constraint | SENSITIVE: requires special handling  

**NOTE:** This schema is an iterative draft (MVP).  
**Focus:** Data integrity and history independence (snapshots).  
**WIP:** Deletion logic and edge cases will be refined during implementation.  

> **Quick Jump:** [Users & Roles](#1-users--roles) | [Exercises & Catalog](#2-exercises--catalog) | [Templates](#3-training-templates) | [History](#4-training-history) | [Access](#5-access-control)

### 1. USERS & ROLES
```rust
// --- Relationships ---
role (1) ---- (0..*) user_account : "defines_permissions"


// [x]
role {
    UUIDv7 id PK
    VARCHAR(100) name UK NN
    VARCHAR(255) description NULL
    VARCHAR(100) slug UK NN
    TIMESTAMPTZ created_at NN DEFAULT CURRENT_TIMESTAMP
    TIMESTAMPTZ updated_at NN DEFAULT CURRENT_TIMESTAMP
}

// [x]
user_account {
    UUIDv7 id PK
    VARCHAR(255) name NULL
    VARCHAR(255) email NN
    VARCHAR(255) password NN SENSITIVE
    BOOLEAN is_active NN DEFAULT true
    BOOLEAN is_superuser NN DEFAULT false
    UUIDv7 role_id FK role.id ON DELETE RESTRICT
    TIMESTAMPTZ created_at NN DEFAULT CURRENT_TIMESTAMP
    TIMESTAMPTZ updated_at NN DEFAULT CURRENT_TIMESTAMP

    // DB Constraint: ensures email uniqueness regardless of case
    RULE uq_user_email UNIQUE (LOWER(email))
}
```
### 2. EXERCISES & CATALOG
```rust
// --- Relationships ---
user_account (0..1) ---- (0..*) exercises : "owns"

equipment (1) ---- (0..*) exercise_equipment : "provides"
exercises (1) ---- (0..*) exercise_equipment : "requires"

muscle_groups (1) ---- (0..*) exercise_primary_muscles : "targets"
exercises     (1) ---- (0..*) exercise_primary_muscles : "stresses_primary"

muscle_groups (1) ---- (0..*) exercise_secondary_muscles : "assists"
exercises     (1) ---- (0..*) exercise_secondary_muscles : "stresses_secondary"

exercise_tags (1) ---- (0..*) exercise_tag_map : "categorizes"
exercises     (1) ---- (0..*) exercise_tag_map : "tagged_with"


// [x]
equipment {
    SMALLINT id PK IDENTITY
    VARCHAR(100) name UK NN
}

// [x]
muscle_groups {
    SMALLINT id PK IDENTITY
    VARCHAR(100) name UK NN
}

// [x]
exercise_tags {
    SMALLINT id PK IDENTITY
    VARCHAR(100) name UK NN
}

// [x]
exercises {
    UUIDv7 id PK
    VARCHAR(100) name NN
    VARCHAR(100) slug UK NULL // Unique when present
    ENUM force NULL // pull | push | static
    ENUM difficulty_level NN // beginner | intermediate | expert
    ENUM mechanic NULL // compound | isolation
    ENUM category NN // strength | stretching | cardio | etc.
    TEXT instructions NULL
    VARCHAR(512) image_path_start NULL
    VARCHAR(512) image_path_end NULL
    BOOLEAN is_system_default NN DEFAULT false
    UUIDv7 created_by FK user_account.id ON DELETE CASCADE NULL
    BOOLEAN is_active NN DEFAULT true // Hidden from search if false
    TIMESTAMPTZ created_at NN DEFAULT CURRENT_TIMESTAMP
    TIMESTAMPTZ updated_at NN DEFAULT CURRENT_TIMESTAMP

    // Logical Isolation: separates system defaults from user custom exercises
    RULE uq_user_exercise UNIQUE (name, created_by) WHERE created_by IS NOT NULL AND is_active IS TRUE
    RULE uq_sys_exerc_slug UNIQUE (slug) WHERE is_system_default IS TRUE
    RULE uq_sys_exerc_name UNIQUE (name) WHERE is_system_default IS TRUE

    INDEX idx_ex_filters ON (is_system_default, is_active)

    /* DESIGN NOTE on idx_ex_filters:
       The effectiveness of this index depends on the distribution of data.
       It is primarily intended to isolate the global system catalog from
       a potentially large volume of user-generated content.
    */
}

// --- Association Tables (M2M Relationships) ---

// [x]
exercise_equipment {
    UUIDv7 exercise_id FK PK ON DELETE CASCADE
    SMALLINT equipment_id FK PK ON DELETE CASCADE

    INDEX idx_ex_equ_id ON (equipment_id)
}

// [x]
exercise_primary_muscles {
    UUIDv7 exercise_id FK PK ON DELETE CASCADE
    SMALLINT muscle_group_id FK PK ON DELETE CASCADE

    INDEX idx_ex_pri_mus_id ON (muscle_group_id)
}

// [x]
exercise_secondary_muscles {
    UUIDv7 exercise_id FK PK ON DELETE CASCADE
    SMALLINT muscle_group_id FK PK ON DELETE CASCADE

    INDEX idx_ex_sec_mus_id ON (muscle_group_id)
}

// [x]
exercise_tag_map {
    UUIDv7  exercise_id FK PK ON DELETE CASCADE
    SMALLINT tag_id FK PK ON DELETE CASCADE

    INDEX idx_ex_tag_id ON (tag_id)
}
```
### 3. TRAINING TEMPLATES
```rust
// --- Relationships ---
user_account (1) ---- (0..*) training_units : "owns"
user_account (1) ---- (0..*) training_plans : "owns"

training_units (1) ---- (0..*) training_unit_exercises : "consists_of"
exercises      (0..1) ---- (0..*) training_unit_exercises : "template_for"

training_plans (1) ---- (0..*) training_plan_units : "contains"
training_units (1) ---- (0..*) training_plan_units : "scheduled_as"


// []
training_units {
    UUIDv7 id PK
    VARCHAR(100) name NN
    UUIDv7 created_by FK user_account.id ON DELETE SET NULL
    ENUM sharing_status NN DEFAULT 'private' // private | shared | public
    TIMESTAMPTZ created_at NN DEFAULT CURRENT_TIMESTAMP
    TIMESTAMPTZ updated_at NN DEFAULT CURRENT_TIMESTAMP
    TEXT description NULL
    UNIQUE (created_by, name)
}

// []
training_plans {
    UUIDv7 id PK
    VARCHAR(100) name NN
    UUIDv7 created_by FK user_account.id ON DELETE SET NULL
    ENUM difficulty_level NN // beginner | intermediate | expert
    ENUM sharing_status NN DEFAULT 'private' // private | shared | public
    TIMESTAMPTZ created_at NN DEFAULT CURRENT_TIMESTAMP
    TIMESTAMPTZ updated_at NN DEFAULT CURRENT_TIMESTAMP
    TEXT description NULL
    UNIQUE (created_by, name)
}

// []
training_unit_exercises {
    INTEGER id PK
    UUIDv7 training_unit_id FK ON DELETE CASCADE
    UUIDv7 exercise_id FK ON DELETE SET NULL
    VARCHAR(100) exercise_name_snapshot NN // Copy from exercise for template stability
    ENUM mode NN // reps | time | distance | sets_only
    SMALLINT order_index NN
    TEXT unit_exercise_notes NULL
    NUMERIC target_weight NULL
    SMALLINT sets NN DEFAULT 1
    SMALLINT reps_min NULL
    SMALLINT reps_max NULL
    SMALLINT target_time_seconds NULL
    NUMERIC target_distance_km NULL
    SMALLINT rest_seconds NULL // Rest between sets
    UNIQUE (training_unit_id, order_index)

    // Mode Consistency: ensures required fields for selected training mode
    RULE check_mode_consistency CHECK (
         (mode = 'reps' AND (reps_min IS NOT NULL OR reps_max IS NOT NULL)) OR
         (mode = 'time' AND target_time_seconds IS NOT NULL) OR
         (mode = 'distance' AND target_distance_km IS NOT NULL) OR
         (mode = 'sets_only' AND
             reps_min IS NULL AND
             reps_max IS NULL AND
             target_time_seconds IS NULL AND
             target_distance_km IS NULL)
    )
    RULE check_sets_count CHECK (sets > 0)
    RULE check_reps_range CHECK (reps_min <= reps_max)
}

// []
training_plan_units {
    INTEGER id PK
    UUIDv7 training_plan_id FK ON DELETE CASCADE
    UUIDv7 training_unit_id FK ON DELETE RESTRICT
    SMALLINT day_number NN
    SMALLINT order_index NN // Sequence in training day
    UNIQUE (training_plan_id, day_number, order_index)

    /* DESIGN NOTE on day_number:
       Gapless day sequence (e.g., 1, 2, 3...) is NOT enforced by the database.
       The application layer is responsible for presenting days in order
       and managing the user experience around rest days or non-sequential plans.
    */
}
```
### 4. TRAINING HISTORY
```rust
// --- Relationships ---
user_account (1) ---- (0..*) training_sessions : "records"
training_sessions (1) ---- (0..*) training_session_exercises : "includes"

exercises (0..1) ---- (0..*) training_session_exercises : "tracks"
training_unit_exercises (0..1) ---- (0..*) training_session_exercises : "fulfills"

training_session_exercises (1) ---- (0..*) training_session_sets : "contains"


// []
training_sessions {
    UUIDv7 id PK
    UUIDv7 user_id FK user_account.id ON DELETE RESTRICT
    UUIDv7 training_plan_id FK ON DELETE SET NULL
    UUIDv7 training_unit_id FK ON DELETE SET NULL

    /* APP LOGIC REMINDER:
       The application MUST correctly handle NULL values for training_plan_id and training_unit_id.
       This occurs in two cases:
       1. The user performs a workout without a pre-defined plan (a "freestyle" session).
       2. The original plan/unit was deleted after the session was completed.
       Analytics and history views should not break in these scenarios.
    */

    VARCHAR(100) plan_name_snapshot NULL // Plan name at start time
    VARCHAR(100) unit_name_snapshot NULL // Name of the workout day (e.g. "Chest/Triceps")
    TIMESTAMPTZ start_time NN DEFAULT CURRENT_TIMESTAMP
    TIMESTAMPTZ end_time NULL
    VARCHAR(50) user_timezone NN // e.g., Europe/Berlin
    ENUM status NN DEFAULT 'in_progress' // in_progress | completed | aborted
    INTEGER duration_seconds NULL // APP LOGIC: Calculate as (end_time - start_time) on status change to 'completed'
    TEXT notes NULL
    INDEX idx_ts_user_start ON (user_id, start_time)
}

// []
training_session_exercises {
    BIGINT id PK
    UUIDv7 training_session_id FK ON DELETE CASCADE
    UUIDv7 exercise_id FK ON DELETE SET NULL
    INTEGER planned_unit_exercise_id FK training_unit_exercises.id ON DELETE SET NULL // Template reference
    ENUM mode_snapshot NN // Copy from template
    VARCHAR(100) exercise_name_snapshot NN // Сopy from exercise
    SMALLINT order_index NN
    SMALLINT order_index_snapshot NULL
    NUMERIC target_weight_snapshot NULL
    SMALLINT sets_snapshot NULL
    SMALLINT reps_min_snapshot NULL
    SMALLINT reps_max_snapshot NULL
    SMALLINT target_time_seconds_snapshot NULL
    NUMERIC target_distance_km_snapshot NULL
    SMALLINT rest_seconds_snapshot NULL

    UNIQUE (training_session_id, order_index)
}

// []
training_session_sets {
    BIGINT id PK
    BIGINT session_exercise_id FK training_session_exercises.id ON DELETE CASCADE
    SMALLINT order_index NN
    NUMERIC weight NULL // Optional for all modes
    SMALLINT reps_completed NULL
    SMALLINT time_seconds NULL
    NUMERIC distance_km NULL
    UNIQUE (session_exercise_id, order_index)


    /* IMPLEMENTATION NOTE (Reordering Logic):
       When reordering records (sets) within an exercise, to avoid a UNIQUE constraint
       conflict on the order_index field, use temporary negative values or a delete/re-insert logic
       within a single transaction.
    */

    /* APP LOGIC REMINDER: Mode-Performance Alignment
       The database does not enforce a match between the exercise mode (reps/time/dist)
       and the set metrics.
       The APPLICATION LAYER (Pydantic/API) MUST:
       1. Check the 'mode_snapshot' in the parent 'training_session_exercises'.
       2. Validate that the user ONLY provides values for the corresponding metric:
          - If mode='reps'     -> only 'reps_completed' allowed.
          - If mode='time'     -> only 'time_seconds' allowed.
          - If mode='distance' -> only 'distance_km' allowed.
       3. Reject the request (422 Unprocessable Entity) if multiple or
          mismatched metrics are provided.
    */

    // Set Performance Consistency: enforces a single primary metric (reps, time, or distance) per set
    RULE check_set_performance CHECK (
        (reps_completed >= 0 AND time_seconds IS NULL AND distance_km IS NULL) OR
        (time_seconds > 0 AND reps_completed IS NULL AND distance_km IS NULL) OR
        (distance_km > 0 AND reps_completed IS NULL AND time_seconds IS NULL) OR
        (reps_completed IS NULL AND time_seconds IS NULL AND distance_km IS NULL)
    )

    /* DESIGN NOTE on check_set_performance:
       This constraint intentionally forbids hybrid metrics within a single set
       (e.g., completing X reps in Y time). It enforces data purity by forcing
       the choice of a single primary metric (reps, time, or distance) per set.
       This simplifies analytics. If hybrid metrics are required in the future,
       this constraint must be revisited.
    */
}
```
### 5. ACCESS CONTROL
```rust
// --- Relationships ---
training_units (1) ---- (0..*) training_unit_access : "governs"
training_plans (1) ---- (0..*) training_plan_access : "governs"

user_account (1) ---- (0..*) training_unit_access : "authorizes (granted_by)"
user_account (1) ---- (0..*) training_plan_access : "authorizes (granted_by)"

user_account (1) ---- (0..*) training_unit_access : "receives (user_id)"
user_account (1) ---- (0..*) training_plan_access : "receives (user_id)"

/* DESIGN NOTE on Access Model:
   Access is governed by two complementary systems:
   1. The `sharing_status` on `training_units` and `training_plans` handles broad access ('private' vs. 'public').
   2. These `*_access` tables manage explicit, granular permissions for specific users when a plan/unit
       has a `sharing_status` of 'shared'. The application layer should check both places
       to determine if a user can access a resource.
*/

// []
training_unit_access {
    UUIDv7 training_unit_id FK PK ON DELETE CASCADE
    UUIDv7 user_id FK user_account.id PK ON DELETE CASCADE // The one who gets access
    UUIDv7 granted_by FK user_account.id ON DELETE SET NULL // The one who gives access
    ENUM access_level NN DEFAULT read // read | write
    TIMESTAMPTZ created_at NN DEFAULT CURRENT_TIMESTAMP

    // Logical protection: users cannot share plans with themselves
    RULE check_not_self_grant CHECK (user_id <> granted_by)
}

// []
training_plan_access {
    UUIDv7 training_plan_id FK PK ON DELETE CASCADE
    UUIDv7 user_id FK user_account.id PK ON DELETE CASCADE // The one who gets access
    UUIDv7 granted_by FK user_account.id ON DELETE SET NULL // The one who gives access
    ENUM access_level NN DEFAULT read // read | write
    TIMESTAMPTZ created_at NN DEFAULT CURRENT_TIMESTAMP

    // Logical protection: users cannot share plans with themselves
    RULE check_not_self_grant CHECK (user_id <> granted_by)
}
```
</details>

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