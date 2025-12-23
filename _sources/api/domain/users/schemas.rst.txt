User Domain Schemas
===================

Pydantic Data Transfer Objects (DTOs) for the Users sub-domain.

Utility Definitions
-------------------

.. autoclass:: app.domain.users.schemas.RoleSlug
    :members: SUPERUSER, FITNESS_TRAINER
    :undoc-members:

.. data:: app.domain.users.schemas.valid_pwd
    :annotation: str

    **Password requirements:** Minimum eight characters, at least one uppercase letter, one lowercase letter, one number, and one special character (``@$!%*?&_``).

---

User Information Models
-----------------------

.. autopydantic_model:: app.domain.users.schemas.User
    :model-signature-prefix: class

.. autopydantic_model:: app.domain.users.schemas.UserAuth
    :model-signature-prefix: class

---

User CRUD Models
----------------

.. autopydantic_model:: app.domain.users.schemas.UserCreate
    :model-signature-prefix: class

.. autopydantic_model:: app.domain.users.schemas.UserUpdate
    :model-signature-prefix: class

---

User Authentication Models
--------------------------

.. autopydantic_model:: app.domain.users.schemas.AccountRegister
    :model-signature-prefix: class

.. automethod:: app.domain.users.schemas.AccountRegister.check_passwords_match

.. autopydantic_model:: app.domain.users.schemas.PasswordUpdate
    :model-signature-prefix: class

---

Role Management Models
----------------------

.. autopydantic_model:: app.domain.users.schemas.UserRoleAdd
    :model-signature-prefix: class

.. autopydantic_model:: app.domain.users.schemas.UserRoleRevoke
    :model-signature-prefix: class
