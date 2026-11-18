Accounts Schemas
================

Shared Definitions
------------------

.. autoclass:: app.domain.accounts.schemas.RoleSlug
   :members: SUPERUSER, FITNESS_TRAINER
   :undoc-members:

.. autoclass:: app.domain.accounts.schemas.PasswordValidator

Page Envelopes
--------------

.. autoclass:: app.domain.accounts.schemas.UserPage
   :undoc-members:
   :inherited-members:

User Information Models
-----------------------

.. autoclass:: app.domain.accounts.schemas.User
   :undoc-members:

.. autoclass:: app.domain.accounts.schemas.UserAuth
   :undoc-members:

Self-Service Input Models
-------------------------

.. autopydantic_model:: app.domain.accounts.schemas.AccountRegister
   :field-show-constraints: false
   :model-show-validator-summary: false
   :field-list-validators: false

.. autopydantic_model:: app.domain.accounts.schemas.PasswordUpdate
   :field-show-constraints: false

Administrative Input Models
---------------------------

.. autopydantic_model:: app.domain.accounts.schemas.UserCreate
   :field-show-constraints: false

.. autopydantic_model:: app.domain.accounts.schemas.UserUpdate
   :field-show-constraints: false
   :inherited-members: UserCreate

.. autopydantic_model:: app.domain.accounts.schemas.UserRoleAdd
   :field-show-constraints: false

.. autopydantic_model:: app.domain.accounts.schemas.UserRoleRevoke
   :field-show-constraints: false
   :inherited-members: UserRoleAdd
