IronTrack
=========

.. image:: https://img.shields.io/badge/python-3.12-3776ab.svg?logo=python&logoColor=white
    :target: https://www.python.org/downloads/
.. image:: https://img.shields.io/badge/FastAPI-009688.svg?logo=fastapi&logoColor=white
    :target: https://fastapi.tiangolo.com/
.. image:: https://img.shields.io/badge/Granian-E97033?logo=rust&logoColor=white
    :target: https://github.com/emmett-framework/granian
.. image:: https://img.shields.io/badge/Angie-B33033?logo=nginx&logoColor=white
    :target: https://angie.software
.. image:: https://img.shields.io/badge/ORM-Advanced--Alchemy-edb641?logo=python&logoColor=white
    :target: https://docs.advanced-alchemy.litestar.dev/
.. image:: https://img.shields.io/badge/license-MIT-4bc51d.svg?logo=opensourceinitiative&logoColor=white
    :target: https://opensource.org/licenses/MIT

**IronTrack** is a high-performance, asynchronous backend service built on **FastAPI** and **Advanced-Alchemy**.

It is designed for comprehensive management of workout data, user accounts, and authentication.

---

Key Features
------------

I. Architecture and Design Patterns
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* **Layered Architecture:** Architected with strict separation of concerns: **`domain`** (business logic, controllers, services), **`db`** (models and migrations), **`config`**, and **`lib`** (shared utilities). This ensures high modularity and ease of maintenance.
* **Service and Repository Patterns:** Uses **Advanced-Alchemy** to implement the Service and Repository architectural patterns, ensuring clean, asynchronous **SQLAlchemy** data operations and strict isolation of business logic.
* **Managed DB Migrations (Alembic):** Employs **Alembic** for creating, applying, and reverting versioned database schema migrations.

II. Performance & Optimization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* **Rust-Powered ASGI Server (Granian):** Hosted on **Granian**, a high-performance ASGI server built in Rust, ensuring extremely low latency and high throughput for asynchronous tasks.
* **Optimized JSON Response:** Implements **MsgSpecJSONResponse** to replace the standard **FastAPI** serializer, utilizing the **Msgspec** library for faster JSON encoding of responses.
* **Connection Pool Manager (PgBouncer):** Uses **PgBouncer** for efficient management of the **PostgreSQL** connection pool, enhancing performance in an asynchronous environment.
* **Custom ASGI Middleware:** A custom handler implemented for accurate request timing, centralized exception interception, and logging of HTTP request metrics.

III. Security & Administration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* **Comprehensive Access Management:** A security system based on Access/Refresh **JWT** tokens delivered via secure HTTP-only cookies. Includes user data caching (**fastapi-cache2**) and Refresh token blacklisting.
* **User Administration (CRUD/RBAC):** Full set of CRUD operations for user accounts, Role-Based Access Control (**RBAC**) supporting `superuser` and `trainer` roles. Supports user cache retention and invalidation.
* **Comprehensive Command Line Interface (CLI):** A centralized entry point built on **Typer**, unifying server start-up, DB migration management (**Advanced-Alchemy** commands), and custom administration tools.

IV. Engineering Practices & CI/CD
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* **Edge Proxy (Angie):** Deployed with **Angie** as a high-performance gateway, handling secure TLS termination and request buffering to protect and offload the application server.
* **CI/CD and Containerization:** Implements multi-stage **Docker** builds (Builder/Runner) and dependency optimization using **uv** (**Astral**). Deployment is fully containerized (`docker-compose`). Automated migration application (**Alembic**) during deployment with service health checks (`healthcheck`).
* **Project Packaging (Hatchling):** Utilizes the modern **Hatchling** tool for project building and packaging.
* **Testing and Code Standards:**
    * **Automated Tests:** Uses **Pytest** and `pytest-databases` to create an isolated, integration testing environment with **transactional rollback** after each test.
    * **Code Standards:** Applies **Ruff** (linter/formatter), **Mypy** (static type checking), and **pre-commit** hooks to ensure code quality and uniformity.
    * **Logging:** Utilizes **Structlog** for structured (**JSON**) logging.

V. Data & Content
~~~~~~~~~~~~~~~~~

* **Rich Default Content:** Includes an automated script (`seeder.py`) to populate the database with **1000 ready-to-use exercises**, along with comprehensive muscle group and equipment directories.

---

Navigation
----------

.. grid:: 2

    .. grid-item-card:: 🚀 Get Started
        :link: usage/installation
        :link-type: doc

        Installation guide and environment setup.

    .. grid-item-card:: 📖 API Reference
        :link: api/index
        :link-type: doc

        Detailed technical documentation of the codebase.

.. toctree::
    :titlesonly:
    :caption: Documentation
    :hidden:

    usage/index
    api/index

.. toctree::
    :titlesonly:
    :caption: Development
    :hidden:

    contribution-guide
    changelog

