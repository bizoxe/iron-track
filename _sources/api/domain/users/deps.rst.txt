User Domain Dependencies
========================

.. automodule:: app.domain.users.deps
   :members: provide_users_service, provide_role_service

.. data:: UserServiceDep
   :annotation: = Annotated[UserService, Depends(provide_users_service)]

   Dependency injection provider for the user service.

.. data:: RoleServiceDep
   :annotation: = Annotated[RoleService, Depends(provide_role_service)]

   Dependency injection provider for the role service.
