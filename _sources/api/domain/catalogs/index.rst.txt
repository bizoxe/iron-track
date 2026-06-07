Catalogs Domain
===============

This domain manages reference data, including equipment, exercise tags, and muscle groups.

---

API Endpoints (Controllers)
---------------------------
FastAPI routers defining the public API for catalog management.

.. toctree::
    :maxdepth: 2

    controllers/equipment
    controllers/exercise_tags
    controllers/muscle_groups

---

Core Components (Services and DTOs)
-----------------------------------
Implementation of business logic and data transfer objects.
We use a hybrid approach:
- ``Pydantic`` for input validation and FastAPI integration.
- ``msgspec.Struct`` for high-performance serialization and data transport.

.. toctree::
    :maxdepth: 1

    services
    schemas

---

Supporting Modules (Utilities and Dependencies)
-----------------------------------------------
Dependency Injection and Filtering Utilities for Catalog Resources.

.. toctree::
    :maxdepth: 1

    deps
    filters
