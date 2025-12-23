Users Domain
============

This domain encapsulates all logic related to user accounts, authentication, and role-based access control.

---

API Endpoints (Controllers)
---------------------------
FastAPI routers defining the public API for users management and access control.

.. toctree::
    :maxdepth: 2
    :titlesonly:
    :hidden:

    controllers/access
    controllers/users
    controllers/user_role

---

Core Components (Services and Schemas)
--------------------------------------
Business logic implementation and Pydantic Data Transfer Objects (DTOs).

.. toctree::
    :maxdepth: 1
    :titlesonly:
    :hidden:

    services
    schemas

---

Supporting Modules (Authentication and Utilities)
-------------------------------------------------
Helpers, dependencies, and JWT-related functionality.

.. toctree::
    :maxdepth: 1
    :titlesonly:
    :hidden:

    auth
    utils
    deps
    jwt_helpers
