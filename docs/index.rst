IronTrack
=========

.. image:: https://img.shields.io/badge/python-3.12-3776ab.svg?logo=python&logoColor=white
    :target: https://www.python.org/downloads/
.. image:: https://img.shields.io/badge/FastAPI-009688.svg?logo=fastapi&logoColor=white
    :target: https://fastapi.tiangolo.com/
.. image:: https://img.shields.io/badge/license-MIT-4bc51d.svg?logo=opensourceinitiative&logoColor=white
    :target: https://opensource.org/licenses/MIT

**IronTrack** is an experimental async backend sandbox for performance testing and constraint-driven architectural experiments.

It is designed to explore architectural patterns, concurrency isolation, and performance trade-offs within a workout tracking domain.
The project focuses on experimentation and benchmarking rather than providing a production-ready solution.

.. note::
   **Infrastructure Context:** This project is intentionally developed and benchmarked on constrained bare-metal hardware (**AMD FX-8320 / HDD**).

   This "high-latency" environment is a deliberate architectural choice. It amplifies performance bottlenecks—such as I/O wait times and serialization overhead—that are often masked by modern cloud infrastructure. This setup forces the evaluation of concurrency patterns and optimization techniques under realistic hardware limitations.

---

Implemented Components
----------------------

I. Architecture and Design Patterns
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* **Layered Structure:** Separation into ``domain`` (logic), ``db`` (models), ``config``, and ``lib`` layers to ensure code maintainability.
* **Repository Pattern:** Decouples business logic from **SQLAlchemy** operations using **Advanced-Alchemy**.
* **Schema Evolution:** Database versioning and migrations via **Alembic**.

II. Performance & Optimization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* **Runtime & Proxy:** Uses **Granian** (Rust-based ASGI) and **Angie** (reverse proxy).
* **Infrastructure Efficiency:** **Bypass TCP stack overhead** via Unix Domain Sockets (UDS) for inter-container communication.
* **Containerization:** Multi-stage **Docker** builds (**Builder/Runner**) with dependency optimization via **uv**.
* **Local Deployment:** Orchestrated via **docker-compose** with automated migrations and service health checks.
* **Serialization:** Fast JSON processing with **msgspec** to minimize response latency.
* **Connection Pooling:** **PgBouncer** integration for efficient database transaction management.

III. Security & Administration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* **Auth System:** Secure JWT (Ed25519) via HTTP-only cookies with token blacklisting and user caching.
* **Access Control (RBAC):** Permission system supporting different user roles (e.g., `superuser`, `trainer`).
* **Unified CLI:** Centralized command-line interface built with **Typer** for server management, migrations, and administrative tools.

IV. Engineering Standards (DX)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* **Type Safety:** Strict static analysis with **Mypy** and runtime validation via **Pydantic v2**.
* **Testing:** Integration suite using **transactional rollbacks** for clean and isolated tests.
* **Code Quality:** Automated linting and formatting via **Ruff** and **pre-commit**.
* **Observability:** Structured logging with **structlog** and request correlation IDs.

V. Data & Content
~~~~~~~~~~~~~~~~~

* **Automated Seeding:** Built-in infrastructure to populate the database with a catalog of 1000+ exercises and reference directories.

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


