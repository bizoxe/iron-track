Accounts Dependencies
=====================

.. automodule:: app.domain.accounts.deps
   :members:

.. data:: UserServiceDep
   :annotation: = Annotated[UserService, Depends(provide_users_service)]

   Injectable ``UserService`` scoped to the request.

.. data:: RoleServiceDep
   :annotation: = Annotated[RoleService, Depends(provide_roles_service)]

   Injectable ``RoleService`` scoped to the request.
