JWT Token Utilities
===================

Data Schemas
------------

.. autoclass:: app.domain.accounts.jwt_helpers.TokenPayloadBase
   :members:
   :undoc-members:

.. autoclass:: app.domain.accounts.jwt_helpers.TokenPayloadAccess
   :show-inheritance:
   :undoc-members:

.. autoclass:: app.domain.accounts.jwt_helpers.TokenPayloadRefresh
   :show-inheritance:
   :undoc-members:

JWT Operations
--------------

.. autofunction:: app.domain.accounts.jwt_helpers.create_access_token
.. autofunction:: app.domain.accounts.jwt_helpers.create_refresh_token
.. autofunction:: app.domain.accounts.jwt_helpers.get_access_token_payload
.. autofunction:: app.domain.accounts.jwt_helpers.get_refresh_token_payload

Token Management & Revocation
-----------------------------

.. autofunction:: app.domain.accounts.jwt_helpers.get_unverified_jti
.. autofunction:: app.domain.accounts.jwt_helpers.add_token_to_blacklist
.. autofunction:: app.domain.accounts.jwt_helpers.is_token_in_blacklist
