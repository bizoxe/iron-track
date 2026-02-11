User Domain Schemas
===================

Pydantic & Struct Data Transfer Objects (DTOs) for the Users sub-domain.

Utility Definitions
-------------------

.. autoclass:: app.domain.users.schemas.RoleSlug
    :members: SUPERUSER, FITNESS_TRAINER
    :undoc-members:

.. autoclass:: app.domain.users.schemas.PasswordValidator

---

User Information Models
-----------------------

.. autoclass:: app.domain.users.schemas.User
    :undoc-members:

.. autoclass:: app.domain.users.schemas.UserAuth
    :undoc-members:

---

User CRUD Models
----------------

.. autopydantic_model:: app.domain.users.schemas.UserCreate

.. autopydantic_model:: app.domain.users.schemas.UserUpdate

---

User Authentication Models
--------------------------

.. autopydantic_model:: app.domain.users.schemas.AccountRegister
   :field-show-constraints: false
   :model-show-validator-summary: false
   :field-list-validators: false
   :model-show-validator-members: false

.. automethod:: app.domain.users.schemas.AccountRegister.check_passwords_match

.. autopydantic_model:: app.domain.users.schemas.PasswordUpdate
   :field-show-constraints: false

---

Role Management Models
----------------------

.. autopydantic_model:: app.domain.users.schemas.UserRoleAdd

.. autopydantic_model:: app.domain.users.schemas.UserRoleRevoke
   :model-show-field-summary: false
   :inherited-members: UserRoleAdd

