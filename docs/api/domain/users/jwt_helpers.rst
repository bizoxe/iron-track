JWT Token Utilities
===================

Utility functions and data schemas for JWT lifecycle management.

Data Schemas
------------

.. autoclass:: app.domain.users.jwt_helpers.TokenPayloadBase
   :members:
   :undoc-members:

.. autoclass:: app.domain.users.jwt_helpers.TokenPayloadAccess
   :show-inheritance:
   :undoc-members:

   *Inherits all claims from* :class:`TokenPayloadBase`.

.. autoclass:: app.domain.users.jwt_helpers.TokenPayloadRefresh
   :show-inheritance:
   :undoc-members:

   *Inherits all claims from* :class:`TokenPayloadBase`.

JWT Operations
--------------

.. autofunction:: app.domain.users.jwt_helpers.create_access_token
.. autofunction:: app.domain.users.jwt_helpers.create_refresh_token
.. autofunction:: app.domain.users.jwt_helpers.get_access_token_payload
.. autofunction:: app.domain.users.jwt_helpers.get_refresh_token_payload

Token Management & Revocation
-----------------------------

.. autofunction:: app.domain.users.jwt_helpers.get_unverified_jti
.. autofunction:: app.domain.users.jwt_helpers.add_token_to_blacklist
.. autofunction:: app.domain.users.jwt_helpers.is_token_in_blacklist


