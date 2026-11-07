Accounts
========

This domain encapsulates all logic related to user account management, authentication and token lifecycle, role-based access control, and administrative access to user-created exercises.

API Endpoints (Controllers)
---------------------------

FastAPI routers defining the public API for authentication and account self-service, user administration, and role assignment and revocation.

.. toctree::
    :maxdepth: 2

    controllers/access
    controllers/users
    controllers/user_roles

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

Authentication and service dependencies, resource filtering, JWT identity management, and account utilities.

.. toctree::
    :maxdepth: 1

    auth
    deps
    filters
    jwt_helpers
    utils
