Exercises
=========

This domain encapsulates all logic related to exercise management and categorization, the distinction between system-wide and user-defined custom exercises with their visibility and ownership rules, and scope-aware filtering.

API Endpoints (Controllers)
---------------------------

FastAPI routers defining the public API for CRUD operations on custom exercises and for mutable, non-deletable system exercises.

.. toctree::
    :maxdepth: 1

    controllers

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

Service dependencies, scope-aware filtering, and exercise utilities.

.. toctree::
    :maxdepth: 1

    deps
    filters
    utils
