Authentication & Authorization
==============================

.. autoclass:: app.domain.accounts.auth.Authenticate
   :members:

---

Internal Data Loading & Cache
-----------------------------

.. automethod:: app.domain.accounts.auth.Authenticate._get_user_from_payload
   :noindex:

   .. note::
      **Cache Strategy:** The result is cached per user (TTL is bound to the access token lifetime)
      to minimize database load. Consistency is maintained via **automatic invalidation** hooks
      triggered by:

      * Logout and self-service profile actions.
      * Role changes.
      * Administrative modifications to user accounts.
