<div align="center">
  <a href="https://github.com/bizoxe/iron-track">
    <img src="docs/_static/logo.svg" width="350" alt="IronTrack Logo">
  </a>

  <h3>Asynchronous workout tracking API built with FastAPI and PostgreSQL.</h3>
</div>

---

[![Docs](https://img.shields.io/badge/docs-view%20now-blue.svg?style=flat&logo=sphinx)](https://bizoxe.github.io/iron-track/)
[![CI Status](https://github.com/bizoxe/iron-track/actions/workflows/ci.yaml/badge.svg)](https://github.com/bizoxe/iron-track/actions/workflows/ci.yaml)
[![Coverage Status](https://codecov.io/gh/bizoxe/iron-track/branch/main/graph/badge.svg)](https://codecov.io/gh/bizoxe/iron-track)
[![Release Status](https://github.com/bizoxe/iron-track/actions/workflows/release.yaml/badge.svg)](https://github.com/bizoxe/iron-track/actions/workflows/release.yaml)

[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Mypy](https://img.shields.io/badge/types-Mypy-3776ab.svg?logo=python&logoColor=white)](https://github.com/python/mypy)
[![Docs Quality](https://github.com/bizoxe/iron-track/actions/workflows/docs.yaml/badge.svg)](https://github.com/bizoxe/iron-track/actions/workflows/docs.yaml)

[![Python 3.12](https://img.shields.io/badge/python-3.12-3776ab.svg?logo=python&logoColor=white)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Advanced Alchemy](https://img.shields.io/badge/Advanced_Alchemy-24292e?style=flat&logo=litestar&logoColor=white)](https://docs.advanced-alchemy.litestar.dev/)
[![License: MIT](https://img.shields.io/badge/license-MIT-3776ab.svg)](https://opensource.org/licenses/MIT)

---

## ✨ Key Features

* ⚡ **Backend**: **FastAPI**, **Asyncpg** and **PgBouncer** for high-concurrency performance.
* 🏗️ **Architecture**: **Repository pattern** powered by **Advanced Alchemy** (SQLAlchemy).
* 📦 **Data**: **1000+ real exercises** and reference data included in **JSON** for rapid initialization.
* 🛡️ **Quality**: Strict **Mypy** typing, **Pydantic v2** validation, and structured logging via **structlog**.
* ⚙️ **Tooling**: Project management with **uv**, linting via **Ruff**, and automated **pre-commit** hooks.

---

## 🛠 Tech Stack

| Category              | Technology                                                                                                                                              |
|:----------------------|:--------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Language**          | [Python 3.12+](https://www.python.org/) (Typed, Async)                                                                                                  |
| **Framework**         | [FastAPI](https://fastapi.tiangolo.com/)                                                                                                                |
| **ORM & Repository**  | [Advanced Alchemy](https://docs.advanced-alchemy.litestar.dev/latest/)                                                                                  |
| **Logging**           | [structlog](https://www.structlog.org/)                                                                                                                 |
| **Package Manager**   | [uv](https://github.com/astral-sh/uv)                                                                                                                   |
| **Database**          | [PostgreSQL](https://www.postgresql.org/)                                                                                                               |
| **Connection Pooler** | [PgBouncer](https://www.pgbouncer.org/)                                                                                                                 |
| **Migrations**        | [Alembic](https://alembic.sqlalchemy.org/)                                                                                                              |
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
cp .env.local src/app/config/.env
```

### 3. Security Setup (JWT Keys)
The application requires RSA private and public keys for authentication.

* **Generate Online**: Use the [JSEncrypt demo](https://travistidwell.com/jsencrypt/demo/) to create a pair (ensure you save them in **PEM** format).
* **Generate via OpenSSL**: Follow the detailed guide in [src/app/certs/README.md](src/app/certs/README.md) (ensure you have **OpenSSL** installed).
* **Setup**: Place the keys in `src/app/certs/` with the following **exact names**:
  * `jwt-private.pem` (Private Key)
  * `jwt-public.pem` (Public Key)

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

### 5. Run Server
```bash
app server dev
```

> [!TIP]
> Once started, the API will be available at http://127.0.0.1:8000.
>
> Explore the interactive docs at http://127.0.0.1:8000/docs.

---

## 📂 Project Structure

```text
├── src/app/   # Application core and business logic.
├── deploy/    # Infrastructure and deployment setup (PostgreSQL, PgBouncer, etc.).
├── docs/      # Sphinx documentation source files.
└── tests/     # Unit and integration tests.
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