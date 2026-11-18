Catalogs
========

This domain encapsulates reference data management for equipment, exercise tags, and muscle groups, the full item lifecycle of creation, update, retirement, and restoration.

API Endpoints (Controllers)
---------------------------

FastAPI routers defining the public API for equipment, exercise tag, and muscle group management.

.. toctree::
    :maxdepth: 2

    controllers/equipment
    controllers/exercise_tags
    controllers/muscle_groups

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

Supporting Modules
------------------

Service dependencies and resource filtering.

.. toctree::
    :maxdepth: 1

    deps
    filters
