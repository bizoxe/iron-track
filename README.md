<div align="center">
  <a href="https://github.com/bizoxe/iron-track">
    <img src="docs/_static/logo.svg" width="350" alt="IronTrack Logo">
  </a>

  <h3>Experimental async backend sandbox built for architectural exploration and performance analysis</h3>
  <p>Focused on concurrency patterns, database optimization, and constraint-driven experiments within a workout tracking domain.</p>
</div>

---

[![CI Status](https://github.com/bizoxe/iron-track/actions/workflows/ci.yaml/badge.svg)](https://github.com/bizoxe/iron-track/actions/workflows/ci.yaml)
[![Coverage Status](https://img.shields.io/codecov/c/github/bizoxe/iron-track?token=NRYTRRO512&logo=codecov&logoColor=white)](https://codecov.io/gh/bizoxe/iron-track)
[![Release Status](https://github.com/bizoxe/iron-track/actions/workflows/release.yaml/badge.svg)](https://github.com/bizoxe/iron-track/actions/workflows/release.yaml)
[![Docs](https://img.shields.io/badge/docs-view%20now-blue.svg?style=flat&logo=sphinx&logoColor=white)](https://bizoxe.github.io/iron-track/)

[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776ab?logo=python&logoColor=white)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-4bc51d?logo=opensourceinitiative&logoColor=white)](https://opensource.org/licenses/MIT)

---

## 🎯 Why

**IronTrack** is an architectural sandbox built around a realistic domain model.\
The workout tracking domain provides sufficient complexity to model real-world interactions (authentication, RBAC, complex relational data), serving as a foundation for honing skills in designing maintainable and extensible systems.

> [!NOTE]
> The project is intentionally benchmarked on constrained hardware (**AMD FX-8320 | HDD**) to evaluate architectural behavior and stability beyond "cloud-ideal" conditions.
>
> Testing under high I/O latency and CPU contention highlights bottlenecks that are typically masked by modern high-performance infrastructure.

> [!IMPORTANT]
> This is a **learning and exploration project**, not a production-driven business application.
>
> Technical solutions (such as PgBouncer, Angie, structured logging) and optimizations (e.g., custom Response via msgspec.json at the FastAPI level) are implemented to study the interaction between the application and the infrastructure layer, and the behavior of the system under load.

#### Project Focus:

* **Managed Complexity and Maintainability**  
    A modular monolith: a single deployable partitioned into domain modules with one-directional, contract-based dependencies;
    each module owns its tables and logic, so changes stay local instead of rippling across the codebase.
* **Holistic System View**  
    The project intentionally includes key infrastructure components (such as a reverse proxy, a connection pooler) to move beyond just application code.
    The goal is to analyze how different layers interact and influence the application's performance and stability, not to build a high-load system.
* **Performance & Efficiency Experiments**  
    Benchmarking on constrained hardware:
    * Makes it easier to identify and analyze bottlenecks and design load scenarios.
    * Forces the writing of resource-efficient code.
* **Decision-Making Culture**    
    Decisions are recorded as Architectural Decision Records — written reasoning instead of remembered reasoning:
    * the act of writing forces context, alternatives, and trade-offs to be stated, not assumed;
    * months later, the "why" behind a constraint or policy remains documented — the primary reader of an ADR is your future self.

---

**Inspiration & Standards**    
> The project conventions, structure, DX workflows, Sphinx documentation generation, and several architectural solutions were borrowed from **litestar-org** public repositories and adapted for this project.  
>
> While the project's foundation is heavily inspired by these practices, the choice of **FastAPI** was a deliberate decision made to explore its ecosystem and constraints. The detailed rationale is documented in the [Tech Stack Rationale | Web Layer Selection](./dev/adr/stack-rationale.md).

<details>
<summary><b>What's Inside for You</b></summary>

Below is a brief list of implementations that may be useful to the community as examples of solving specific technical tasks.

**Important:** These implementations do not claim to be universally optimal for every use case. They represent my personal experience in solving tasks within this specific stack and are intended to serve as a starting point for your own projects.

#### Security & Auth

* **Scenario:** Event Loop blocking during password hashing.\
**Approach:** Offloading CPU-bound Argon2 hashing to a dedicated `ThreadPoolExecutor`.\
**Code:** [src/app/lib/crypt.py](src/app/lib/crypt.py)
* **Scenario:** JWT signing performance overhead (RSA-2048).\
**Approach:** Migrating to Ed25519 (EdDSA) signatures via joserfc.\
**Code:** [src/app/lib/jwt_utils.py](src/app/lib/jwt_utils.py)
* **Scenario:** Lack of native support for HTTP-only Cookie authorization in standard Swagger UI (OpenAPI) docs.\
**Approach:** Custom `JWTCookieSecurity` implementation inheriting from `SecurityBase` that correctly propagates cookie metadata to the OpenAPI schema.\
**Code:** [src/app/lib/auth.py](src/app/lib/auth.py)
* **Scenario:** Lack of instant JWT-refresh token revocation.\
**Approach:** **JTI Blacklisting** mechanism integrated with Redis/Valkey.\
**Code:** [src/app/domain/accounts/auth.py](src/app/domain/accounts/auth.py) and [src/app/domain/accounts/jwt_helpers.py](src/app/domain/accounts/jwt_helpers.py)  

#### Performance

* **Scenario:** Network stack overhead during inter-container traffic.\
**Approach:** Orchestration via Unix Domain Sockets (UDS) to bypass the TCP stack overhead in inter-container communication.\
**Code:** [docker-compose.yaml](docker-compose.yaml)
* **Scenario:** JSON serialization bottlenecks (FastAPI `jsonable_encoder` overhead).\
**Approach:** Response layer based on `msgspec` to reduce serialization overhead with automatic **CamelCase** conversion for frontend compatibility.\
**Code:** [src/app/lib/json_response.py](src/app/lib/json_response.py) and [src/app/lib/schema.py](src/app/lib/schema.py)  

#### Database & Caching

* **Scenario:** SQLAlchemy + asyncpg behind PgBouncer in transaction pooling mode.\
**Approach:** Single pooling tier: PgBouncer owns connection reuse, the engine runs `NullPool`, and asyncpg's prepared statement cache stays enabled — the well-known advice to zero it out predates PgBouncer's prepared statement tracking and sacrifices the performance benefits of prepared statement caching.\
**Code:** [src/app/config/base.py](src/app/config/base.py)
* **Scenario:** Password synchronization between PostgreSQL and PgBouncer.\
**Approach:** Makefile script for automated `userlist.txt` generation directly from PostgreSQL system tables.\
**Code:** [Makefile](Makefile)
* **Scenario:** Excessive DB load from redundant permission checks in every request.\
**Approach:** Granular caching of `UserAuth` entities in Valkey with automated invalidation.\
**Code:** [src/app/domain/accounts/auth.py](src/app/domain/accounts/auth.py) and [src/app/domain/accounts/utils.py](src/app/domain/accounts/utils.py)

#### Observability & Monitoring

* **Scenario:** Impact of heavy I/O logging on the application's main event loop.\
**Approach:** Non-blocking logging pipeline using `QueueHandler` to offload log writing to a background thread.\
**Code:** [src/app/server/observability/setup.py](src/app/server/observability/setup.py) and [src/app/server/observability/handlers.py](src/app/server/observability/handlers.py)
* **Scenario:** Difficulties in debugging distributed requests and linking logs across different layers.\
**Approach:** Request correlation via `Correlation ID` (Middleware -> Service -> Repository -> DB query logs).\
**Code:** [src/app/server/core.py](src/app/server/core.py), [src/app/server/observability/setup.py](src/app/server/observability/setup.py) and [src/app/server/observability/handlers.py](src/app/server/observability/handlers.py)

#### Developer Experience (DX)

* **Scenario:** Database pollution after tests and slow CI pipelines.\
**Approach:** **Transactional Pytest** pattern (automatic transaction rollback after each test).\
**Code:** [tests/integration/conftest.py](tests/integration/conftest.py)
* **Scenario:** Management overhead of multiple commands for server, migrations, and DB ops.\
**Approach:** Unified CLI interface built with `Typer`, consolidating server commands, `advanced-alchemy` tools, and custom scripts.\
**Code:** [src/app/main.py](src/app/main.py) and [src/app/server/server_cli.py](src/app/server/server_cli.py)
* **Scenario:** Documentation noise from internal ORM fields and unreadable `Annotated` type signatures.\
**Approach:** Custom Sphinx hooks for automated signature cleaning and SQLAlchemy internal attribute filtering.\
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

The data layer is designed, not accumulated. The blueprint below is the design-time view of the full schema — users/RBAC,
exercises, templates, history, access — together with the cross-cutting **DELETION POLICY** and **ADMIN ACCESS** matrices.

<details>
<summary><b>View Database Blueprint</b></summary>

<br>

#### Schema Version: v0.1 | Last Updated: 2026-11
#### STATUS: [x] implemented | [~] partial | [ ] planned  
#### NOTATION: PK: PRIMARY KEY | FK: FOREIGN KEY | UK: UNIQUE | NN: NOT NULL | UUIDv7: UUID version 7 | SENSITIVE: requires special handling

**NOTE:** This blueprint is a design-time view, not the runtime source of truth.
Applied migrations are authoritative; in case of conflict, migrations win.
Any migration change must update this blueprint in the same PR.

**Focus:** Data integrity and history independence (snapshots).

### BLUEPRINT CONVENTIONS

**General:**
  
`0. ENUM TYPES` — the sole normative source of enum names and values.

`uq_*` = unique constraint · `uidx_*` = unique index (partial/functional) · `idx_*` = index · `chk_*` = check.

**Tables:**
 * columns: compact notation `TYPE NAME MODIFIERS // comment`\
  (an ENUM column comment starts with the physical type name);
 * named constraints: actual PG syntax, inside the table body;
 * indexes: actual PG syntax, as statements immediately following the table body;
 * normative ENUM values are not specified in column comments.

**Relationships** (reading convention for the `// --- Relationships ---`
blocks at the head of each section):

`A (x) ---- (y) B` — left (x) = multiplicity of A per one row of B (`0..1` = nullable FK, `1` = NOT NULL FK / PK member);
right (y) = number of B rows per one A. A reading rule, not a constraint: the multiplicities mirror the FK/PK declarations in the table bodies and must match them.


**ENUM column notation:**

`ENUM <column_name> [NULL|NN] [DEFAULT v] // <physical_enum_type>[: annotation]`

* `ENUM` — marker for an enum-typed column;
* the comment must begin with the physical type name (`*_enum`);
* the normative list of values is defined only in the `ENUM TYPES` section;
* other annotations (`shared with...`, semantics) are free text after the colon.

### DELETION POLICY (cross-cutting)
**Principles:** history is immutable; losing an owner ≠ losing data; PII leaves the system only through scheduled jobs.

#### Conventions
| Pattern                                               | Meaning                                                                                                   |
|-------------------------------------------------------|-----------------------------------------------------------------------------------------------------------|
| `deleted_at TIMESTAMPTZ NULL`                         | soft delete; NULL = live (catalogs, user_account)                                                         |
| uniqueness on soft-deletable catalog **name** columns | partial unique index `WHERE deleted_at IS NULL`; deleted names are reusable                               |
| `user_account.email`                                  | functional unique index (`LOWER(email)`); the email stays **reserved** until JOB A anonymization frees it |

**Note:** Account deletion is soft by default; the owner may retire their own account (self-service); hard purge/anonymization is performed only via JOB A.

#### Matrix
| Data                 | When the owner disappears (JOB A)               | Note                                                                    |
|----------------------|-------------------------------------------------|-------------------------------------------------------------------------|
| custom exercise      | SET NULL → orphan zone; reaped by JOB B         | `chk_exercise_system_no_author` legalizes the orphan zone               |
| training_unit / plan | SET NULL; Step 1 sweeps private ones explicitly | partial UK on non-NULL owners                                           |
| training_session*    | RESTRICT → forces anonymize path                | immutable facts                                                         |
| *_access (both FKs)  | CASCADE                                         | both FKs are PK members (NN) → SET NULL impossible → CASCADE            |
| trainer_client       | CASCADE                                         | access relationship; deleting either account removes assignment periods |

**Legend:** 

`SET NULL` applies to nullable ownership columns (`created_by`);\
`CASCADE` to NOT NULL structural links (PK members, `*_access`, `trainer_client`);\
`RESTRICT` protects immutable facts (`training_session.user_id`).

**Trade-off (accepted):** after an owner disappears, references from other users' data may dangle (`created_by IS NULL`, `exercise_id IS NULL`) — an intended state, not a bug: history stays valid via snapshots; ownerless custom exercises are reaped by JOB B; ownerless templates (`created_by IS NULL`) are accepted residue — Step 1 is the only sanctioned template-removal path.

#### Jobs (implementation: with the sessions feature, post-MVP — ADR 02 → Decision 8)
* **JOB A · account purge** (daily, RETENTION=30d): Step 1 — accounts without history
  and with fully-private templates are purged with their content
  (plans → units → customs → account, strict order due to RESTRICT);
  Step 2 — everyone else anonymized (`deleted+<id>@anon.invalid`, password sentinel).
* **JOB B · orphan GC** (weekly): drops ownerless custom exercises unreferenced
  by templates/history. Covers paths outside JOB A (manual/DBA deletions).

**SQL & rationale:** [Data Deletion Policy & Account Lifecycle](dev/adr/02_adr_data_deletion_policy.md).

### ADMIN ACCESS (cross-cutting)
**Principles:** admins curate content, not personal history; destructive actions
on user content belong to the owner, the scheduled jobs, or admin moderation of
exposed (shared/public) templates; No administrative API role grants access to training sessions.

**Rationale:** read on user content exists for support/diagnostics; scoped
delete on exposed (shared/public) templates exists for moderation; user
content is never edited by admins; sessions are outside both axes.
The superuser is deliberately excluded from user-area endpoints (See: §1 APP-RULE (role scoping)).
Rights are evaluated on the root entity;
reading a template covers its nested graph (units ↔ exercises) — nested
objects carry no separate admin rights.

| Object                                            | Admin rights                                                | Note                                                                                                      |
|---------------------------------------------------|-------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------|
| system exercises (incl. tags, images)             | read + edit                                                 | never delete (ADR 02 → Decision 2)                                                                        |
| catalogs (`equipment`, `muscle_group`, `tag`)     | read + edit + retire                                        | retire = soft delete (`deleted_at`) only                                                                  |
| user custom exercises                             | read only                                                   | delete → owner / JOB B only; exposure only via referencing templates (See: §2 APP-RULE (curated content)) |
| user templates (`training_unit`, `training_plan`) | read + delete (`sharing_status ≠ 'private'`)                | moderation scope; delete = owner-identical path (same FK behavior); private → owner / JOB A Step 1 only   |
| training sessions                                 | — (no API access)                                           | immutable personal history; debug via DB tooling                                                          |
| orphan exercises                                  | read (orphan-review queue)                                  | reaped by JOB B                                                                                           |
| promotion queue (post-MVP)                        | review / promote                                            | trainer-authored exercises → system catalog (See: §5 `trainer_client`)                                    |
| user accounts                                     | create (provision), read, update, ban / unban (`is_active`) | account lifecycle → DELETION POLICY (JOB A); ban applies to superusers too (except the primary admin)     |

**Enforcement:** role checks centralized in the authz module (slug-based); the `is_superuser`
mirror invariant (§1) keeps the flag a reliable fast-path for queries. 
This matrix survives role expansion: new roles (e.g., `Support`, ...) 
inherit it — none of them may gain session access.
Both admin axes (support-read, moderation-delete) are logged app-side
(actor / target / timestamp).

**Post-MVP** *(directions, not commitments — seeds for future decisions)*:
* "unpublish" (`sharing_status` → `private`) — candidate remedy for the
  moderation gap: a scheduled unit cannot be hard-deleted (RESTRICT → 409)
  while referenced by the owner's plans (See: §3 APP-RULE (template graph));
* structural audit tables on top of app-side logs — candidate if moderation
  volume grows (same pattern as the ADR-02 orphan-review queue);
* report/appeal flow — direction to explore with the product layer
  (notice-and-action), the user-facing counterpart of moderation.


> **Quick Jump:** [Users & Roles](#1-users--roles) | [Exercises & Reference Tables](#2-exercises--reference-tables) | [Templates](#3-training-templates) | [History](#4-training-history) | [Access](#5-access-control)

### 0. ENUM TYPES
```rust
// Used in: exercise
CREATE TYPE force_enum AS ENUM ('pull', 'push', 'static');
CREATE TYPE mechanic_enum AS ENUM ('compound', 'isolation');
CREATE TYPE category_enum AS ENUM (
    'cardio', 
    'olympic_weightlifting', 
    'plyometrics', 
    'powerlifting', 
    'strength', 
    'stretching', 
    'strongman'
);

// Used in: exercise, training_plan
CREATE TYPE difficulty_level_enum AS ENUM ('beginner', 'intermediate', 'expert');

// Used in: exercise_muscle
CREATE TYPE muscle_role_enum AS ENUM ('primary', 'secondary');

// Used in: training_unit, training_plan
CREATE TYPE sharing_status_enum AS ENUM ('private', 'shared', 'public');

// Used in: training_unit_exercise, training_session_exercise
CREATE TYPE unit_exercise_mode_enum AS ENUM ('reps', 'time', 'distance', 'sets_only');

// Used in: training_session
CREATE TYPE session_status_enum AS ENUM ('in_progress', 'completed', 'aborted');
```
### 1. USERS & ROLES
```rust
// --- Relationships ---
role (1) ---- (0..*) user_account : "assigned_to"


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
    VARCHAR(255) email NN // Login identifier
    VARCHAR(255) password NN SENSITIVE
    BOOLEAN is_active NN DEFAULT true // Admin ban
    BOOLEAN is_superuser NN DEFAULT false
    UUIDv7 role_id NN FK ON DELETE RESTRICT
    TIMESTAMPTZ deleted_at NULL // Soft delete; NULL = active
    TIMESTAMPTZ last_activity_at NULL // Last successful login (UTC); NULL = never logged in; drives dormant-account retention (ADR-02)
    TIMESTAMPTZ created_at NN DEFAULT CURRENT_TIMESTAMP
    TIMESTAMPTZ updated_at NN DEFAULT CURRENT_TIMESTAMP
    
    /* 
       APP-RULE (login gate): a user may log in only when is_active = true AND 
       deleted_at IS NULL.
    
       APP-RULE (invariant): is_superuser acts as a fast-path flag.
       The application layer must guarantee that:
       is_superuser == true  <==>  role_id maps to role.slug = superuser.
       The flag is mutated ONLY by role assign/revoke operations — never as a
       standalone toggle (prevents flag/role drift).
       
       APP-RULE (enforcement): destructive actions performed via the admin surface
       on the primary system admin (DEFAULT_ADMIN_EMAIL) and on the acting
       superuser's own account are forbidden. Self-service retirement by the
       account owner is permitted (except for the primary admin). Any OTHER
       superuser may be banned (is_active = false) — ban suffices: access checks
       consult is_active.
       
       APP-RULE (role scoping): an account's role defines its API area.
       User-area endpoints require a user-area role; the superuser is
       deliberately excluded — admins act only through the admin surface and
       never author user content.
    */
}
// --- user_account : indexes ---
// Email uniqueness regardless of case (Case-Insensitive Unique); reserved until JOB A anonymization
CREATE UNIQUE INDEX uidx_user_account_email_lower ON user_account (LOWER(email));
CREATE INDEX idx_user_account_role_id ON user_account (role_id);
```
### 2. EXERCISES & REFERENCE TABLES
```rust
// --- Relationships ---
user_account (0..1) ---- (0..*) exercise : "creates"

equipment (1) ---- (0..*) exercise_equipment : "required_for"
exercise  (1) ---- (0..*) exercise_equipment : "requires"

muscle_group (1) ---- (0..*) exercise_muscle : "targeted_by"
exercise     (1) ---- (0..*) exercise_muscle : "targets"

tag      (1) ---- (0..*) exercise_tag : "categorizes"
exercise (1) ---- (0..*) exercise_tag : "tagged_with"


/* 
   APP-RULE (curated content): 
   - tags and image_*_path (exercise table) are system-exercise content,
     maintained by admins/superusers only;
   - custom exercises carry NO tags and NO images (`image_*_path` stays NULL);
   - equipment/muscle links REMAIN available to custom exercises.
*/

/*
   DESIGN (reference tables): Uniqueness (CREATE UNIQUE INDEX) is enforced only among LIVE rows 
   (WHERE deleted_at IS NULL). Deleted names may be reused or restored.
*/

// [x]
equipment {
    SMALLINT id PK IDENTITY
    VARCHAR(100) name NN
    TIMESTAMPTZ deleted_at NULL // Soft delete; NULL = active
}
// --- equipment : indexes ---
CREATE UNIQUE INDEX uidx_equipment_name ON equipment (name)
    WHERE deleted_at IS NULL;


// [x]
muscle_group {
    SMALLINT id PK IDENTITY
    VARCHAR(100) name NN
    TIMESTAMPTZ deleted_at NULL // Soft delete (see note above)
}
// --- muscle_group : indexes ---
CREATE UNIQUE INDEX uidx_muscle_group_name ON muscle_group (name)
    WHERE deleted_at IS NULL;


// [x]
tag {
    SMALLINT id PK IDENTITY
    VARCHAR(100) name NN
    TIMESTAMPTZ deleted_at NULL // Soft delete (see note above)
}
// --- tag : indexes ---
CREATE UNIQUE INDEX uidx_tag_name ON tag (name)
    WHERE deleted_at IS NULL;


// [x]
exercise {
    UUIDv7 id PK
    VARCHAR(100) name NN
    VARCHAR(100) slug NN
    ENUM force NULL // force_enum
    ENUM difficulty_level NN // difficulty_level_enum: shared with training_plan
    ENUM mechanic NULL // mechanic_enum
    ENUM category NN // category_enum
    TEXT instructions NULL
    VARCHAR(512) image_start_path NULL // Relative CDN path, leading '/', join: CDN_BASE_URL.rstrip('/') + path
    VARCHAR(512) image_end_path NULL // Same contract as image_start_path
    BOOLEAN is_system_default NN DEFAULT false
    UUIDv7 created_by FK user_account.id ON DELETE SET NULL
    TIMESTAMPTZ created_at NN DEFAULT CURRENT_TIMESTAMP
    TIMESTAMPTZ updated_at NN DEFAULT CURRENT_TIMESTAMP
    
    /* 
       APP-RULE: Ownerless custom exercises (created_by IS NULL, is_system_default = false)
       are invisible in ALL listings; visible only in admin orphan-review queue.
       
       DESIGN: One-directional ownership check legalizes the ORPHAN zone
       (created_by IS NULL AND NOT is_system_default) produced by account purge.
       Orphans are invisible in listings (APP-RULE) and reaped by JOB B (See: DELETION POLICY).
    */
    
    // System exercises never have an author; ownerless customs are ALLOWED (post-purge)
    CONSTRAINT chk_exercise_system_no_author CHECK (
        NOT is_system_default OR created_by IS NULL
    ) 
}
// --- exercise : indexes ---
// Uniqueness for live users only; orphans are excluded
CREATE UNIQUE INDEX uidx_exercise_created_by_slug ON exercise (created_by, slug)
    WHERE created_by IS NOT NULL;

// Uniqueness for core global system content
CREATE UNIQUE INDEX uidx_exercise_system ON exercise (slug)
    WHERE is_system_default IS TRUE;


// --- Association Tables (M2M Relationships) ---

// [x]
exercise_equipment {
    UUIDv7 exercise_id FK PK ON DELETE CASCADE
    SMALLINT equipment_id FK PK ON DELETE CASCADE
}
// --- exercise_equipment : indexes ---
CREATE INDEX idx_exercise_equipment_equipment_id ON exercise_equipment (equipment_id);


// [x]
exercise_muscle {
    UUIDv7 exercise_id FK PK ON DELETE CASCADE
    SMALLINT muscle_group_id FK PK ON DELETE CASCADE
    ENUM muscle_role NN // muscle_role_enum
    
    /*
       DESIGN: PK excludes muscle_role: the same muscle cannot be both
       primary and secondary for one exercise.
    */
}
// --- exercise_muscle : indexes ---
CREATE INDEX idx_exercise_muscle_muscle_group_id_muscle_role ON exercise_muscle (muscle_group_id, muscle_role);


// [x]
exercise_tag {
    UUIDv7  exercise_id FK PK ON DELETE CASCADE
    SMALLINT tag_id FK PK ON DELETE CASCADE
}
// --- exercise_tag : indexes ---
CREATE INDEX idx_exercise_tag_tag_id ON exercise_tag (tag_id);
```
### 3. TRAINING TEMPLATES
```rust
// --- Relationships ---
user_account (0..1) ---- (0..*) training_unit : "creates"
user_account (0..1) ---- (0..*) training_plan : "creates"

training_unit (1) ---- (0..*) training_unit_exercise : "contains"
exercise      (0..1) ---- (0..*) training_unit_exercise : "source_exercise"

training_plan (1) ---- (0..*) training_plan_unit : "contains"
training_unit (1) ---- (0..*) training_plan_unit : "scheduled_as"


/* 
   APP-RULE (template graph):
   - a training unit or training plan may be public only if its entire
     template graph references system exercises exclusively;
   - a shared training unit or training plan may reference custom exercises.
     Those exercises are readable only by users who have access to the containing template;
   - a training_plan may reference only the plan owner's training_units (API validation). 
     Another user's unit is never referenced directly:
     it is cloned into the user's own catalog first, then scheduled (See: §5 APP-RULE (Clone-on-use)).
*/


// []
training_unit {
    UUIDv7 id PK
    VARCHAR(100) name NN
    UUIDv7 created_by FK user_account.id ON DELETE SET NULL
    UUIDv7 source_unit_id FK training_unit.id ON DELETE SET NULL // Source unit; informational only
    ENUM sharing_status NN DEFAULT 'private' // sharing_status_enum: shared with training_plan
    TIMESTAMPTZ created_at NN DEFAULT CURRENT_TIMESTAMP
    TIMESTAMPTZ updated_at NN DEFAULT CURRENT_TIMESTAMP
    TEXT description NULL
}
// --- training_unit : indexes ---
CREATE UNIQUE INDEX uidx_training_unit_created_by_name ON training_unit (created_by, name)
    WHERE created_by IS NOT NULL;

// []
training_plan {
    UUIDv7 id PK
    VARCHAR(100) name NN
    UUIDv7 created_by FK user_account.id ON DELETE SET NULL
    UUIDv7 source_plan_id FK training_plan.id ON DELETE SET NULL // Source plan; informational only
    ENUM difficulty_level NN // difficulty_level_enum: shared with exercise
    ENUM sharing_status NN DEFAULT 'private' // sharing_status_enum: shared with training_unit
    TIMESTAMPTZ created_at NN DEFAULT CURRENT_TIMESTAMP
    TIMESTAMPTZ updated_at NN DEFAULT CURRENT_TIMESTAMP
    TEXT description NULL
}
// --- training_plan : indexes ---
CREATE UNIQUE INDEX uidx_training_plan_created_by_name ON training_plan (created_by, name)
    WHERE created_by IS NOT NULL;

// []
training_unit_exercise {
    BIGINT id PK IDENTITY
    UUIDv7 training_unit_id FK ON DELETE CASCADE
    UUIDv7 exercise_id FK ON DELETE SET NULL
    VARCHAR(100) exercise_name_snapshot NN // Copy from exercise for template stability
    ENUM mode NN // unit_exercise_mode_enum: shared with training_session_exercise.mode_snapshot
    SMALLINT order_index NN
    TEXT unit_exercise_notes NULL
    NUMERIC(5,2) target_weight NULL // kg, max 999.99
    SMALLINT sets NN DEFAULT 1
    SMALLINT reps_min NULL
    SMALLINT reps_max NULL
    SMALLINT target_time_seconds NULL
    NUMERIC(6,3) target_distance_km NULL // km, max 999.999, 1 m precision
    SMALLINT rest_seconds NULL // Rest between sets
    
    /* 
       APP-RULE: Unit Exercise Ordering
       The order of exercises within a training unit is user-editable
       and may be reordered.
    */
    
    // Required metric present, foreign metrics absent
    CONSTRAINT chk_training_unit_exercise_mode_consistency CHECK (
        CASE mode
            WHEN 'time'     THEN target_time_seconds IS NOT NULL
                             AND target_distance_km IS NULL
                             AND reps_min IS NULL AND reps_max IS NULL
            WHEN 'distance' THEN target_distance_km IS NOT NULL
                             AND target_time_seconds IS NULL
                             AND reps_min IS NULL AND reps_max IS NULL
            WHEN 'sets_only' THEN reps_min IS NULL AND reps_max IS NULL
                             AND target_time_seconds IS NULL
                             AND target_distance_km IS NULL
            WHEN 'reps'     THEN target_time_seconds IS NULL
                             AND target_distance_km IS NULL
                             AND (reps_min IS NOT NULL OR reps_max IS NOT NULL)
                             AND (reps_min IS NULL OR reps_max IS NULL OR reps_min <= reps_max)
            ELSE FALSE
        END
    )
    CONSTRAINT chk_training_unit_exercise_positive_sets CHECK (sets > 0)
    CONSTRAINT chk_training_unit_exercise_positive_order CHECK (order_index > 0)
    CONSTRAINT chk_training_unit_exercise_nonnegative_targets CHECK (
        (target_weight IS NULL OR target_weight >= 0)
        AND (target_time_seconds IS NULL OR target_time_seconds > 0)
        AND (target_distance_km IS NULL OR target_distance_km > 0)
        AND (rest_seconds IS NULL OR rest_seconds >= 0)
    )
    // Allows swapping order_index inside one transaction
    CONSTRAINT uq_training_unit_exercise_unit_order
        UNIQUE (training_unit_id, order_index) DEFERRABLE INITIALLY IMMEDIATE
}
// --- training_unit_exercise : indexes ---
CREATE INDEX idx_training_unit_exercise_exercise_id ON training_unit_exercise (exercise_id);

// []
training_plan_unit {
    BIGINT id PK IDENTITY
    UUIDv7 training_plan_id FK ON DELETE CASCADE
    UUIDv7 training_unit_id FK ON DELETE RESTRICT
    SMALLINT day_number NN
    SMALLINT order_index NN // Sequence in training day
    
    /* 
       APP-RULE: Plan Unit Ordering
       The order of training units within a training plan day is user-editable
       and may be reordered.
    */
    
    /* 
       APP-RULE (invariant):
       Gapless day sequence (e.g., 1, 2, 3...) is NOT enforced by the database.
       The application layer is responsible for presenting days in order
       and managing the user experience around rest days or non-sequential plans.
    */
    
    CONSTRAINT chk_training_plan_unit_positive_position
        CHECK (day_number > 0 AND order_index > 0)
    // Allows swapping order_index in day inside one transaction
    CONSTRAINT uq_training_plan_unit_plan_day_order
        UNIQUE (training_plan_id, day_number, order_index) DEFERRABLE INITIALLY IMMEDIATE
}
// --- training_plan_unit : indexes ---
CREATE INDEX idx_training_plan_unit_unit_id ON training_plan_unit (training_unit_id);
```
### 4. TRAINING HISTORY
```rust
// --- Relationships ---
user_account (1) ---- (0..*) training_session : "records"
training_session (1) ---- (0..*) training_session_exercise : "includes"

exercise (0..1) ---- (0..*) training_session_exercise : "tracks"
training_unit_exercise (0..1) ---- (0..*) training_session_exercise : "fulfills"

training_session_exercise (1) ---- (0..*) training_session_set : "contains"


// []
training_session {
    UUIDv7 id PK
    UUIDv7 user_id FK user_account.id ON DELETE RESTRICT
    UUIDv7 training_plan_id FK ON DELETE SET NULL
    UUIDv7 training_unit_id FK ON DELETE SET NULL
    VARCHAR(100) plan_name_snapshot NULL // Plan name at start time
    VARCHAR(100) unit_name_snapshot NULL // Name of the workout day (e.g. "Chest/Triceps")
    TIMESTAMPTZ start_time NN DEFAULT CURRENT_TIMESTAMP
    TIMESTAMPTZ end_time NULL
    VARCHAR(50) user_timezone NN // e.g., Europe/Berlin
    ENUM status NN DEFAULT 'in_progress' // session_status_enum
    TEXT notes NULL
    
    /* 
       APP-RULE: Optional Session Origin
       A session may be created without a training plan or training unit
       (freestyle workout). History and analytics must handle NULL references correctly.
    */
    
    CONSTRAINT chk_training_session_time_order
        CHECK (end_time IS NULL OR end_time >= start_time)
    CONSTRAINT chk_training_session_status_end_time
        CHECK (
            (status = 'in_progress' AND end_time IS NULL)
            OR
            (status IN ('completed', 'aborted') AND end_time IS NOT NULL)
        )
}
// --- training_session : indexes ---
// Ensures a user can have only one active session
CREATE UNIQUE INDEX uidx_training_session_user_active
    ON training_session (user_id) WHERE status = 'in_progress';
CREATE INDEX idx_training_session_user_id_start_time 
    ON training_session (user_id, start_time);
CREATE INDEX idx_training_session_training_plan_id ON training_session (training_plan_id);
CREATE INDEX idx_training_session_training_unit_id ON training_session (training_unit_id);


// []
training_session_exercise {
    BIGINT id PK IDENTITY
    UUIDv7 training_session_id FK ON DELETE CASCADE
    UUIDv7 exercise_id FK ON DELETE SET NULL
    BIGINT planned_unit_exercise_id FK training_unit_exercise.id ON DELETE SET NULL // Template reference
    SMALLINT order_index NN // Live execution order; user-editable while in_progress (see APP-RULE below)
    VARCHAR(100) exercise_name_snapshot NN // Copy from exercise for template stability
    // Snapshots from training_unit_exercise at session creation
    ENUM mode_snapshot NN // unit_exercise_mode_enum: shared with training_unit_exercise.mode
    SMALLINT order_index_snapshot NULL
    TEXT unit_exercise_notes_snapshot NULL
    NUMERIC(5,2) target_weight_snapshot NULL
    SMALLINT sets_snapshot NULL
    SMALLINT reps_min_snapshot NULL
    SMALLINT reps_max_snapshot NULL
    SMALLINT target_time_seconds_snapshot NULL
    NUMERIC(6,3) target_distance_km_snapshot NULL
    SMALLINT rest_seconds_snapshot NULL
    
    /* 
       APP-RULE: Session Exercise Ordering
       While a training session is in_progress, exercise order may be changed.
       After the session becomes completed or aborted, exercise order is treated
       as historical and is not changed by normal editing.
    */

    CONSTRAINT chk_training_session_exercise_positive_order 
        CHECK (order_index > 0)
    // Allows swapping order_index inside one transaction
    CONSTRAINT uq_training_session_exercise_session_order
        UNIQUE (training_session_id, order_index) DEFERRABLE INITIALLY IMMEDIATE
}
// --- training_session_exercise : indexes ---
CREATE INDEX idx_training_session_exercise_exercise_id ON training_session_exercise (exercise_id);
CREATE INDEX idx_training_session_exercise_unit_exercise_id 
    ON training_session_exercise (planned_unit_exercise_id);

// []
training_session_set {
    BIGINT id PK IDENTITY
    BIGINT session_exercise_id FK training_session_exercise.id ON DELETE CASCADE
    SMALLINT order_index NN
    NUMERIC(5,2) weight NULL // kg, max 999.99
    SMALLINT reps_completed NULL
    SMALLINT time_seconds NULL
    NUMERIC(6,3) distance_km NULL // km, max 999.999, 1 m precision
    
    /* 
       APP-RULE: Session Set Ordering
       Set order represents execution order and is not normally reorderable.
       Corrections to historical data, if supported, are explicit history edits.
    */
    
    /* 
       APP-RULE: Mode-Performance Alignment
       The application must validate set metrics against the
       mode_snapshot of the parent training_session_exercise.

       reps     -> reps_completed only
       time     -> time_seconds only
       distance -> distance_km only

       The database does not enforce this cross-table invariant.
    */
    
    CONSTRAINT uq_training_session_set_exercise_order
        UNIQUE (session_exercise_id, order_index)
    CONSTRAINT chk_training_session_set_positive_order CHECK (order_index > 0)
    CONSTRAINT chk_training_session_set_weight CHECK (weight IS NULL OR weight >= 0)
    CONSTRAINT chk_training_session_set_performance CHECK (
        (reps_completed >= 0 AND time_seconds IS NULL AND distance_km IS NULL) OR
        (time_seconds > 0 AND reps_completed IS NULL AND distance_km IS NULL) OR
        (distance_km > 0 AND reps_completed IS NULL AND time_seconds IS NULL) OR
        (reps_completed IS NULL AND time_seconds IS NULL AND distance_km IS NULL)
    )
    
    /* 
       DB INVARIANT: Set Performance Consistency
       A set contains at most one primary performance metric:
       reps, time, or distance.
       Hybrid metrics are intentionally not supported.
       This keeps set data unambiguous and simplifies analytics.
    */
}
```
### 5. ACCESS CONTROL
```rust
// --- Relationships ---
training_unit (1) ---- (0..*) training_unit_access : "has access grants"
training_plan (1) ---- (0..*) training_plan_access : "has access grants"

user_account (0..1) ---- (0..*) training_unit_access : "grants access (granted_by)"
user_account (0..1) ---- (0..*) training_plan_access : "grants access (granted_by)"

user_account (1) ---- (0..*) training_unit_access : "receives access (user_id)"
user_account (1) ---- (0..*) training_plan_access : "receives access (user_id)"

user_account (1) ---- (0..*) trainer_client : "trains (trainer)"
user_account (1) ---- (0..*) trainer_client : "trained_by (client)"


/* 
   DESIGN on Access Model:
   Access is determined by the resource's sharing_status together with
   explicit per-user grants stored in the corresponding *_access table.

   sharing_status defines the access policy:
     - private: only the resource owner (created_by) can access it;
     - shared: the owner and explicitly granted users can access it;
     - public: any authenticated user can access it.

   The *_access tables store explicit per-user access grants for resources
   in the 'shared' mode.

   Access grants confer read-only visibility of the original template and
   the right to clone it (Clone-on-use); they never transfer ownership
   or edit rights over the original.

   Client access is governed SEPARATELY by trainer_client (relationship grants):
   an active assignment (revoked_at IS NULL) gives the trainer read-only access 
   to the client's training sessions and progress — NOT to the client's private content 
   (templates, custom exercises). Relationship grants are independent of sharing_status 
   and *_access in both directions. Assignment lifecycle is admin-managed in MVP
   (self-serve invites are post-MVP).

   A client MAY have several concurrently active trainers; every active
   assignment grants the same read-only scope.
*/

/*
   APP-RULE on Clone-on-use:
   Access resolution (read & clone), first match wins:
   owner (created_by) -> superuser -> sharing_status='public' ->
   explicit *_access grant (sharing_status='shared') -> denied (uniform 404).
   Trainer/client assignments play NO role in template access.

   NOTE: Superuser powers are defined cross-cutting (See: ADMIN ACCESS).

   Clone graph policy:
   - system exercises are referenced as-is (never cloned);
   - custom exercises of the original owner are DEEP-CLONED into the
     recipient's catalog (slug collisions resolved by suffixing);
   - public templates contain only system exercises (API validation),
     so their clones never deep-copy;
   - provenance: training_plan.source_plan_id / training_unit.source_unit_id,
     populated for all clones (informational, ON DELETE SET NULL).
*/

/*
   APP-RULE (grantor integrity):
   granted_by is always set server-side to the authenticated grantor;
   the resource owner never receives explicit access rows for their own
   resource (owner is resolved first in the access chain).
   chk_*_access_grantor_not_recipient is redundant guard:
   granted_by IS NULL means the grantor's account was hard-deleted
   (SET NULL) — self-grant is then impossible by construction.
*/

// []
training_unit_access {
    UUIDv7 training_unit_id FK PK ON DELETE CASCADE
    UUIDv7 user_id FK user_account.id PK ON DELETE CASCADE // The user receiving access
    UUIDv7 granted_by FK user_account.id ON DELETE SET NULL // The user granting access
    TIMESTAMPTZ created_at NN DEFAULT CURRENT_TIMESTAMP

    CONSTRAINT chk_training_unit_access_grantor_not_recipient
        CHECK (granted_by IS NULL OR user_id <> granted_by)
}
// --- training_unit_access : indexes ---
CREATE INDEX idx_training_unit_access_user_id ON training_unit_access (user_id);

// []
training_plan_access {
    UUIDv7 training_plan_id FK PK ON DELETE CASCADE
    UUIDv7 user_id FK user_account.id PK ON DELETE CASCADE // The user receiving access
    UUIDv7 granted_by FK user_account.id ON DELETE SET NULL // The user granting access
    TIMESTAMPTZ created_at NN DEFAULT CURRENT_TIMESTAMP

    CONSTRAINT chk_training_plan_access_grantor_not_recipient
        CHECK (granted_by IS NULL OR user_id <> granted_by)
}
// --- training_plan_access : indexes ---
CREATE INDEX idx_training_plan_access_user_id ON training_plan_access (user_id);

// []
trainer_client {
    BIGINT id PK IDENTITY
    UUIDv7 trainer_id NN FK user_account.id ON DELETE CASCADE
    UUIDv7 client_id NN FK user_account.id ON DELETE CASCADE
    TIMESTAMPTZ assigned_at NN DEFAULT CURRENT_TIMESTAMP // Period start
    TIMESTAMPTZ revoked_at  NULL // Period end; NULL = active assignment
    
    /*
       DESIGN: assignment lifecycle — assign = INSERT (new period),
       revoke = UPDATE revoked_at, reinstate = INSERT new period.
       Physical row deletion permitted (e.g., admin cleanup) but erases
       period history — prefer revocation.
    */
    
    /*
       APP-RULE: Session access resolution (read & analytics), first match wins:
       owner (user_id) -> active trainer of the owner
       (trainer_client: trainer_id = caller, client_id = owner, revoked_at IS NULL)
       -> denied (uniform 404).
       Scope is strictly read-only: sessions, sets, and server-computed
       progress/analytics. Server-side joins over the client's own exercises
       for aggregate computation are NOT entity exposure.
       Superuser is deliberately EXCLUDED here, unlike template resolution —
       see ADMIN ACCESS (sessions are outside the admin API surface).
    */
    
    /*
       Post-MVP: Trainer authoring/management of client training content
       may be introduced as a separate capability. Such capability may
       require an active trainer_client assignment as a prerequisite, but
       trainer_client itself never grants write access to client content.
       
       Trainers author content as REGULAR users (same rules as any account:
       custom exercises without tags/images, templates via sharing_status).
       Promotion of trainer-authored exercises into the system catalog
       (admin-curated queue -> is_system_default = TRUE, created_by -> NULL)
       is a separate post-MVP capability. Trainers never gain authoring
       privileges from the trainer_client relationship itself.
    */

    CONSTRAINT chk_trainer_client_not_self CHECK (trainer_id <> client_id)
}
// --- trainer_client : indexes ---
// At most ONE active assignment per (trainer, client) pair
CREATE UNIQUE INDEX uidx_trainer_client_active ON trainer_client (trainer_id, client_id)
    WHERE revoked_at IS NULL;
CREATE INDEX idx_trainer_client_client_id ON trainer_client (client_id);
```
</details>

---

## 📈 Performance & Efficiency
Testing methodology and benchmark specification: [SPEC.md](./benchmarks/SPEC.md).

**Optimization Highlights:**
* **Authentication:** Migrated JWT signing from RSA-2048 to Ed25519 (cutting the dominant CPU cost of token issuance); offloaded `Argon2id` password hashing to `ThreadPoolExecutor` to prevent Event Loop blocking.
* **Access Control:** Implemented local JTI caching for access-token verification — cache hits skip Ed25519 verification entirely, safe by construction: entries are written only after full verification, and `jti` is `uuid4`, so naming a valid one requires possessing the token.
* **Serialization:** Replaced standard FastAPI/Pydantic JSON with native `msgspec.json` for high-performance output.

*For detailed load testing results, hardware configuration, and flame graphs, see: [Load Testing Report: Authentication & Serialization](benchmarks/auth-serialization.md).*

<details>
<summary><b>View Benchmark Results (Baseline vs Final)</b></summary>

*For each endpoint, three performance states were tracked: Baseline, Intermediate Optimization, and Final.*

<details>
<summary><b>Endpoint: <code>/signup</code></b></summary>

| Metric                | **Baseline** | **Final**     | **Delta**              |
|-----------------------|--------------|---------------|------------------------|
| **Mean Latency**      | 662.76 ms    | **601.42 ms** | **-9.26% (-61.34 ms)** |
| **P90 (90%)**         | 674.30 ms    | **654.34 ms** | **-2.96% (-19.96 ms)** |
| **CPU Load (Core 0)** | 57.55%       | **55.46%**    | **-3.63% (-2.09%)**    |
| **CPU Load (Core 1)** | 57.66%       | **56.51%**    | **-2.00% (-1.15%)**    |

*Analysis: The first optimization phase involved offloading password hashing to a `ThreadPoolExecutor`. This architectural decision successfully prevented Event Loop blocking, ensuring the parallel processing of light and medium-weight incoming requests even during intensive cryptographic computations. In the final stage, a ~9% reduction in mean latency and a slight decrease in CPU load were observed (Baseline → Final). Performance gains were achieved by setting `auto_refresh=False` at the ORM level and switching to native `msgspec.json` serialization. However, `Argon2id` cryptography remains the primary limiting factor. It is worth noting that since this endpoint handles a small data payload, the performance delta between custom implementations and FastAPI’s standard serialization is negligible in this specific context.*

---
*The full iterative report, including all intermediate steps, flame graphs, and full metric sets, is available in the linked report.*
</details>

<details>
<summary><b>Endpoint: <code>/signin</code></b></summary>

| Metric                | **Baseline** | **Final**     | **Delta**               |
|-----------------------|--------------|---------------|-------------------------|
| **Mean Latency**      | 857.39 ms    | **520.95 ms** | **-39.2% (-336.44 ms)** |
| **P90 (90%)**         | 1100.00 ms   | **676.86 ms** | **-38.5% (-423.14 ms)** |
| **CPU Load (Core 0)** | 58.76%       | **33.31%**    | **-43.3% (-25.45%)**    |
| **CPU Load (Core 1)** | 59.04%       | **34.18%**    | **-42.1% (-24.86%)**    |

*Analysis: During the first optimization phase, the computationally heavy `RSA-2048` token signing algorithm was replaced with `Ed25519`. This eliminated Event Loop blocking caused by intensive mathematical operations and reduced per-core CPU load from ~59% to ~36% (a relative reduction of ~39%, or roughly 23 percentage points). In the final optimization, the data loading strategy was modified by limiting the selection of `User` model fields and applying the `noload(m.User.role)` directive, bringing the cumulative reduction in mean latency to ~39% (Baseline → Final). While the ORM optimization improved average latency by reducing I/O and memory overhead, `Argon2id` cryptography remains the deterministic factor, consistent with the findings for the `/signup` endpoint.*

---
*The full iterative report, including all intermediate steps, flame graphs, and full metric sets, is available in the linked report.*
</details>

<details>
<summary><b>Endpoint: <code>/me</code></b></summary>

| Metric                | **Baseline** | **Final**   | **Delta**             |
|-----------------------|--------------|-------------|-----------------------|
| **Mean Latency**      | 3.70 ms      | **2.35 ms** | **-36.5% (-1.35 ms)** |
| **P90 (90%)**         | 4.36 ms      | **3.01 ms** | **-31.0% (-1.35 ms)** |
| **CPU Load (Core 0)** | 44.56%       | **28.93%**  | **-35.1% (-15.63%)**  |
| **CPU Load (Core 1)** | 45.12%       | **30.19%**  | **-33.1% (-14.93%)**  |

*Analysis: During the first phase of optimization, profiling revealed that the cryptographic verification of access token signatures using the `Ed25519` algorithm incurred significant overhead. The final stage included optimizations at both the transport and ORM layers; however, a substantial performance gain and a ~33–35% reduction in CPU load (Baseline → Final) were achieved through local access token caching. This effectively shifted the workload toward I/O-bound operations and application business logic. The `/me` endpoint serves as a baseline for assessing the cost of authentication within the system. Since this authentication mechanism is utilized across all protected endpoints, this optimization provides a **multiplicative effect**, significantly increasing the system's overall throughput and reducing the computational resource requirements per incoming request.*

---
*The full iterative report, including all intermediate steps, flame graphs, and full metric sets, is available in the linked report.*
</details>
</details>

---

## 📂 Project Structure

```text
├── src/app/                       # Application core and business logic.
├── dev/adr/                       # Architecture Decision Records (design rationale and history).
├── deploy/                        # Infrastructure and deployment setup (PostgreSQL, Angie, etc.).
├── benchmarks/                    # Performance testing suite and results.
├── docs/                          # Sphinx documentation source files.
├── Makefile                       # Task runner: setup, dev, quality, docs, infra, release.
├── docker-compose.yaml            # Base runtime stack, production-like (all services).
├── docker-compose.override.yaml   # Dev layer auto-merged over the base (bind-mounted code, hot reload).
├── .env.local.template            # Local environment template for the Quick Start setup.
├── .env.docker.dev.template       # Dockerized stack, development mode (pairs with the override file).
├── .env.docker.template           # Dockerized stack, production-like mode.
├── .env.testing                   # Committed env for the test suite (loaded by tests/conftest.py).
└── tests/                         # Unit and integration tests.
```

---

## 📚 Documentation

Quick Access:

| Document                                                                           | Description                               |
|:-----------------------------------------------------------------------------------|:------------------------------------------|
| [Installation Guide](https://bizoxe.github.io/iron-track/usage/installation.html)  | Step-by-step first-time setup.            |
| [Development Workflow](https://bizoxe.github.io/iron-track/usage/development.html) | Hot-reload, Docker volumes, and Makefile. |
| [CLI Guide](https://bizoxe.github.io/iron-track/usage/cli-guide.html)              | Application management commands.          |
| [Changelog](https://bizoxe.github.io/iron-track/changelog.html)                    | Full history of project changes.          |

---

## 🚀 Quick Start

Ensure you have **[Docker](https://docs.docker.com/get-docker/)**, **[Make](https://www.gnu.org/software/make/)**, and **[uv](https://docs.astral.sh/uv/)** installed.

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
The application uses the **Ed25519** algorithm for secure token signing. This requires a **JWK (JSON Web Key)** stored in your environment configuration.

* **Generate the Key**: Create a new secure key pair using the Makefile shortcut:
```bash
make gen-key
```

* **Setup**:
  * **Copy** the output from the command above.
  * **Open** your `src/app/config/.env` file.
  * **Assign the value** to `JWT_PRIVATE_KEY` wrapped in single quotes:
```bash
# src/app/config/.env
JWT_PRIVATE_KEY='{"crv": "Ed25519", "x": "...", "d": "...", "kty": "OKP"}'
```

> [!NOTE]
> A single Ed25519 JWK contains both the private and public components used for token signing and verification.

### 4. Infrastructure & Data
```bash
# Start PostgreSQL and Valkey
make infra-up

# (Optional) Verify containers are running
docker ps

# Apply migrations (create/update schema)
app database upgrade --no-prompt
# Create system roles (required before first user registration)
app users create-roles
# Optional: seed reference catalogs & exercises
make seed
```

> [!IMPORTANT]
> **Creating roles is mandatory**. You must execute `app users create-roles` before registering any users, as it initializes the base permission system.

### 5. Run Server
```bash
app server dev
```

> [!TIP]
> Once started, the API will be available at http://127.0.0.1:8000.
>
> Explore the interactive docs at http://127.0.0.1:8000/docs.

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
* `app server dev` — Start the development server (**Uvicorn**) with hot-reload enabled.
* `app server run` — Start the server in production-like mode (**Granian**).

### Database & Users
* `app database upgrade [REVISION]` — Apply migrations up to the given revision (default: `head`); add `--no-prompt` to skip the confirmation prompt.
* `app users create-roles` — Initialize mandatory system roles.

</details>

> [!TIP]
> Use `app -h` to explore the built-in CLI and its available commands.

---

**Contributing**

Contributions are welcome! See the [Contributing Guide](CONTRIBUTING.rst).

**License**

Licensed under the [MIT License](LICENSE).