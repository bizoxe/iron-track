User and Role Services
======================

Domain services encapsulating the business logic for User and Role data models.

---

User Service (`UserService`)
----------------------------

.. autoclass:: app.domain.users.services.UserService()
   :no-inherited-members:
   :undoc-members:
   :members: authenticate, update_password, check_critical_action_forbidden, get_users_paginated_dto
   :exclude-members: UserRepository, model_type, repository_type, to_model_on_create, to_model_on_update, match_fields

Role Service (`RoleService`)
----------------------------

.. autoclass:: app.domain.users.services.RoleService()
   :no-inherited-members:
   :members: get_id_and_slug_by_slug, get_default_role
   :exclude-members: RoleRepository, model_type, repository_type, match_fields

