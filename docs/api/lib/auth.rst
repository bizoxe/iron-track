JWT Cookie Security Scheme
==========================

.. autoclass:: app.lib.auth.JWTCookieSecurity

   .. automethod:: app.lib.auth.JWTCookieSecurity.__call__

---

Public Instances
----------------

The following instances of :py:class:`app.lib.auth.JWTCookieSecurity` are exported for use as FastAPI dependencies:

.. data:: app.lib.auth.access_token
   :annotation: = JWTCookieSecurity(authentication_token="access_token")

.. data:: app.lib.auth.refresh_token
   :annotation: = JWTCookieSecurity(authentication_token="refresh_token")
