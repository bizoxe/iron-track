Users Domain
============

This domain encapsulates all logic related to user accounts, authentication, and role-based access control.

---

API Endpoints (Controllers)
---------------------------
FastAPI routers defining the public API for users management and access control.

.. toctree::
    :maxdepth: 2

    controllers/access
    controllers/users
    controllers/user_role

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

Supporting Modules (Authentication and Utilities)
-------------------------------------------------
Core dependencies, JWT identity management, and resource filtering utilities.

.. toctree::
    :maxdepth: 1

    auth
    deps
    filters
    jwt_helpers
    utils
