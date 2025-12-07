"""User Role Management API Endpoints.

Defines the operations for assigning and revoking user roles. Requires superuser privileges.
"""

from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
)

from app.domain.users import urls
from app.domain.users.auth import Authenticate
from app.domain.users.deps import (
    RoleServiceDep,
    UserServiceDep,
)
from app.domain.users.schemas import (
    UserAuth,
    UserRoleAdd,
    UserRoleRevoke,
)
from app.domain.users.utils import check_user_before_modify_role
from app.lib.deps import RedisClientDep
from app.lib.exceptions import ConflictException
from app.lib.invalidate_cache import invalidate_user_cache
from app.lib.json_response import MsgSpecJSONResponse

role_router = APIRouter(
    tags=["User Account Role"],
)


@role_router.patch(
    path=urls.ACCOUNT_ASSIGN_ROLE,
    name="roles:assign",
)
async def assign_new_role(  # noqa: PLR0913
    super_user: Annotated[UserAuth, Depends(Authenticate.superuser_required())],
    users_service: UserServiceDep,
    roles_service: RoleServiceDep,
    redis_client: RedisClientDep,
    user_add_role: UserRoleAdd,
    email: str,
) -> MsgSpecJSONResponse:
    """Assign a new role to the specified user by email.

    This operation requires superuser privileges. **Self-assignment is forbidden**
    (superuser modifying their own account) for security.

    Raises:
        PermissionDeniedException: If the superuser attempts to modify their own account or the system admin.
    """
    user_obj = await check_user_before_modify_role(
        users_service=users_service,
        email=email,
    )
    users_service.check_critical_action_forbidden(
        target_user=user_obj,
        calling_superuser_id=super_user.id,
    )
    new_role = await roles_service.get_id_and_slug_by_slug(slug=user_add_role.role_slug)
    if user_obj.role_id == new_role.id:
        msg = f"User {user_obj.email} already has the '{new_role.slug}' role"
        raise ConflictException(message=msg)

    await users_service.update(data={"role_id": new_role.id}, item_id=user_obj.id)
    await invalidate_user_cache(
        user_id=user_obj.id,
        redis_client=redis_client,
    )
    return MsgSpecJSONResponse(
        content={"message": f"Successfully assigned the '{new_role.slug}' role to {user_obj.email}"},
    )


@role_router.patch(
    path=urls.ACCOUNT_REVOKE_ROLE,
    name="roles:revoke",
)
async def revoke_and_set_default_role(  # noqa: PLR0913
    super_user: Annotated[UserAuth, Depends(Authenticate.superuser_required())],
    users_service: UserServiceDep,
    roles_service: RoleServiceDep,
    redis_client: RedisClientDep,
    user_revoke_role: UserRoleRevoke,
    email: str,
) -> MsgSpecJSONResponse:
    """Revoke the specified role from the user by email and set the default role.

    This operation requires superuser privileges. **Self-assignment is forbidden**
    (superuser modifying their own account) for security.

    Raises:
        PermissionDeniedException: If the superuser attempts to modify their own account or the system admin.
    """
    user_obj = await check_user_before_modify_role(
        users_service=users_service,
        email=email,
    )
    users_service.check_critical_action_forbidden(
        target_user=user_obj,
        calling_superuser_id=super_user.id,
    )
    old_role = await roles_service.get_id_and_slug_by_slug(slug=user_revoke_role.role_slug)
    if old_role.id == user_obj.role_id:
        default_role = await roles_service.get_default_role(
            default_role_slug=users_service.default_role,
        )
        await users_service.update(data={"role_id": default_role.id}, item_id=user_obj.id)
        await invalidate_user_cache(
            user_id=user_obj.id,
            redis_client=redis_client,
        )
        return MsgSpecJSONResponse(
            content={
                "message": (
                    f"Successfully revoked the '{old_role.slug}' role for {user_obj.email} "
                    f"and set to default role '{default_role.slug}'"
                )
            }
        )

    msg = (
        f"User {user_obj.email} currently has the '{user_obj.role_slug}' role, "
        f"which does not match the requested role '{old_role.slug}' for revocation"
    )
    raise ConflictException(message=msg)
