Authentication Utilities
========================

Authentication and authorization utilities.

---

Token Utilities
---------------

.. autofunction:: app.domain.users.auth.get_payload_from_token

---

Public Dependencies
-------------------

.. autoclass:: app.domain.users.auth.Authenticate
   :members: get_current_user, get_current_user_for_refresh, get_current_active_user, superuser_required, trainer_required, get_refresh_jti

---

Internal Mechanisms (Read-Only)
-------------------------------

These functions are internal to the authentication process and should not be called directly.

Cache Strategy
^^^^^^^^^^^^^^

.. automethod:: app.domain.users.auth.Authenticate._get_user_from_payload

   .. attention::
      This method is aggressively cached and is the primary source for loading user authentication data from the database.
      Changes to user roles or status may not be immediately reflected until the cache expires.
