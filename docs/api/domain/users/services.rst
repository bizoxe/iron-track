User and Role Services
======================

Domain services encapsulating the business logic for User and Role data models.

---

User Service (`UserService`)
----------------------------

Bases: :py:class:`advanced_alchemy.extensions.fastapi.service.SQLAlchemyAsyncRepositoryService`\ [:py:class:`~app.db.models.user.User`\]

Handles database operations for users.

Class Configuration
^^^^^^^^^^^^^^^^^^^

**default_role** (`= DEFAULT_USER_ROLE_SLUG`)
   The slug of the role assigned to a new user upon registration.

**system_admin_email** (`= DEFAULT_ADMIN_EMAIL`)
   The email of the primary system administrator, which is protected from destructive actions.

**match_fields** (`= ["email"]`)
   The list of fields used for default user retrieval.

Custom Methods
^^^^^^^^^^^^^^

.. automethod:: app.domain.users.services.UserService.authenticate

.. automethod:: app.domain.users.services.UserService.update_password

.. automethod:: app.domain.users.services.UserService.check_critical_action_forbidden

User Repository (`UserService.UserRepository`)
----------------------------------------------

Bases: :py:class:`advanced_alchemy.extensions.fastapi.repository.SQLAlchemyAsyncRepository`\ [:py:class:`~app.db.models.user.User`\]

User SQLAlchemy Repository.

---

Role Service (`RoleService`)
----------------------------

Bases: :py:class:`advanced_alchemy.extensions.fastapi.service.SQLAlchemyAsyncRepositoryService`\ [:py:class:`~app.db.models.role.Role`\]

Handles database operations for roles.

Class Configuration
^^^^^^^^^^^^^^^^^^^

**match_fields** (`= ["name"]`)
   The list of fields used for default role retrieval.

Custom Methods
^^^^^^^^^^^^^^

.. automethod:: app.domain.users.services.RoleService.get_id_and_slug_by_slug

.. automethod:: app.domain.users.services.RoleService.get_default_role

Role Repository (`RoleService.RoleRepository`)
----------------------------------------------

Bases: :py:class:`advanced_alchemy.extensions.fastapi.repository.SQLAlchemyAsyncRepository`\ [:py:class:`~app.db.models.role.Role`\]

Role SQLAlchemy Repository.
