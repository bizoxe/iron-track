Exercises Domain
================

This domain encapsulates all logic related to exercise management, categorization, and execution tracking.

---

API Endpoints (Controllers)
---------------------------
FastAPI routers defining the public API for managing exercises.

.. toctree::
   :maxdepth: 1
   :titlesonly:
   :hidden:

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
   :titlesonly:
   :hidden:

   services
   schemas

---

Supporting Modules (Utilities and Dependencies)
-----------------------------------------------
Internal helpers, query filters, and shared dependencies.

.. toctree::
   :maxdepth: 1
   :titlesonly:
   :hidden:

   filters
   deps
