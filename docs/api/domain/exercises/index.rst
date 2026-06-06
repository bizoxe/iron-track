Exercises Domain
================

This domain encapsulates all logic related to exercise management and categorization.

---

API Endpoints (Controllers)
---------------------------
FastAPI routers defining the public API for managing exercises.

.. toctree::
   :maxdepth: 1

   controllers

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
Dependency Injection and Filtering Utilities for Exercise Resources.

.. toctree::
   :maxdepth: 1

   filters
   deps
