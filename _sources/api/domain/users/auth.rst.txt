Authentication & Authorization
==============================

Core authentication and authorization dependencies for FastAPI.

.. autoclass:: app.domain.users.auth.Authenticate
   :members:
   :exclude-members: _get_user_from_payload

---

Internal Data Loading & Cache
-----------------------------

.. automethod:: app.domain.users.auth.Authenticate._get_user_from_payload
   :noindex:

   .. note::
      **Cache Strategy:** This method is aggressively cached using Valkey to minimize database pressure.
      Consistency is maintained via **automatic invalidation** hooks triggered by:

      * Password updates.
      * Role changes.
      * Administrative (CRUD) modifications to user records.
