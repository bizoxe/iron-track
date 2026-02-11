Authentication & Authorization
==============================

Core dependencies and utilities for handling user identity and access control.

---

Token Validation & Configuration
--------------------------------

.. data:: app.domain.users.auth.claims_registry
   :annotation: = JWTClaimsRegistry(exp=True, iat=True)

   This registry defines the mandatory claims required for every JWT processed by the system.
   Any token lacking these claims will be rejected with an :class:`~app.lib.exceptions.UnauthorizedException`.

.. autofunction:: app.domain.users.auth.get_payload_from_token

---

Authentication Dependencies
---------------------------

The ``Authenticate`` class provides factory methods that act as FastAPI dependencies.

.. autoclass:: app.domain.users.auth.Authenticate
   :members: get_current_user, get_current_user_for_refresh, get_current_active_user, superuser_required, trainer_required, get_refresh_jti

---

Internal Data Loading
---------------------

.. automethod:: app.domain.users.auth.Authenticate._get_user_from_payload

   .. note::
      **Cache Strategy:** This method is aggressively cached using Redis to minimize database pressure.
      Consistency is maintained via **automatic invalidation** hooks triggered by:

      * Password updates.
      * Role changes.
      * Administrative (CRUD) modifications to user records.
