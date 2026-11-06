"""User Role Endpoints.

Defines the operations for assigning and revoking user roles.
Requires superuser privileges.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from app.config.constants import DEFAULT_USER_ROLE_SLUG
from app.domain.accounts import urls
from app.domain.accounts.auth import Authenticate
from app.domain.accounts.deps import (
    RoleServiceDep,
    UserServiceDep,
)
from app.domain.accounts.schemas import (
    UserAuth,
    UserRoleAdd,
    UserRoleRevoke,
)
from app.domain.accounts.utils import (
    check_critical_action_forbidden,
    invalidate_user_cache,
)
from app.lib.exceptions import ConflictException
from app.lib.json_response import MsgSpecJSONResponse
from app.lib.schema import ErrorInfo

user_roles_router = APIRouter(
    tags=["Accounts: User Roles"],
)


@user_roles_router.patch(
    path=urls.USER_ROLE_ASSIGN,
    operation_id="AssignRole",
    name="roles:assign",
    summary="Assign role",
    responses={
        200: {
            "description": "Updated",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Successfully assigned new role",
                        "details": {
                            "user_id": "550e8400-e29b-41d4-a716-446655440000",
                            "role_slug": "fitness-trainer",
                        },
                    }
                }
            },
        },
        403: {
            "model": ErrorInfo,
        },
        404: {
            "model": ErrorInfo,
        },
        409: {
            "model": ErrorInfo,
        },
    },
)
async def assign_new_role(
    superuser: Annotated[UserAuth, Depends(Authenticate.superuser_required())],
    users_service: UserServiceDep,
    roles_service: RoleServiceDep,
    user_id: UUID,
    user_add_role: UserRoleAdd,
) -> MsgSpecJSONResponse:
    """Assign a new role to the specified user by ID.

    Security restrictions:

    * Self-modification is forbidden.
    * Modifying the primary system administrator account is forbidden.
    """
    user_obj = await users_service.get_and_validate_for_role_change(
        user_id=user_id,
    )
    check_critical_action_forbidden(
        target_user=user_obj,
        calling_superuser_id=superuser.id,
    )
    new_role = await roles_service.get_id_and_slug_by_slug(slug=user_add_role.role_slug)
    if user_obj.role_id == new_role.id:
        raise ConflictException(message="User already has this role")

    users_service.assign_role(user_obj=user_obj, new_role=new_role)
    await invalidate_user_cache(
        user_id=user_obj.id,
    )
    return MsgSpecJSONResponse(
        content={
            "message": "Successfully assigned new role",
            "details": {
                "user_id": str(user_obj.id),
                "role_slug": new_role.slug,
            },
        },
    )


@user_roles_router.patch(
    path=urls.USER_ROLE_REVOKE,
    operation_id="RevokeRole",
    name="roles:revoke",
    summary="Revoke role",
    responses={
        200: {
            "description": "Updated",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Role successfully revoked and default role applied",
                        "details": {
                            "user_id": "550e8400-e29b-41d4-a716-446655440000",
                            "revoked_role": "superuser",
                            "default_role": "application-access",
                        },
                    }
                }
            },
        },
        403: {
            "model": ErrorInfo,
        },
        404: {
            "model": ErrorInfo,
        },
        409: {
            "model": ErrorInfo,
        },
    },
)
async def revoke_and_set_default_role(
    superuser: Annotated[UserAuth, Depends(Authenticate.superuser_required())],
    users_service: UserServiceDep,
    roles_service: RoleServiceDep,
    user_id: UUID,
    user_revoke_role: UserRoleRevoke,
) -> MsgSpecJSONResponse:
    """Revoke the specified role from the user by ID and set the default role.

    Security restrictions:

    * Self-modification is forbidden.
    * Modifying the primary system administrator account is forbidden.
    """
    user_obj = await users_service.get_and_validate_for_role_change(
        user_id=user_id,
    )
    check_critical_action_forbidden(
        target_user=user_obj,
        calling_superuser_id=superuser.id,
    )
    old_role = await roles_service.get_id_and_slug_by_slug(slug=user_revoke_role.role_slug)
    if old_role.id == user_obj.role_id:
        default_role = await roles_service.get_default_role(
            default_role_slug=DEFAULT_USER_ROLE_SLUG,
        )
        users_service.revoke_role(user_obj=user_obj, default_role=default_role)
        await invalidate_user_cache(
            user_id=user_obj.id,
        )
        return MsgSpecJSONResponse(
            content={
                "message": "Role successfully revoked and default role applied",
                "details": {
                    "user_id": str(user_obj.id),
                    "revoked_role": old_role.slug,
                    "default_role": default_role.slug,
                },
            }
        )
    msg = "The user does not currently have the requested role for revocation"
    raise ConflictException(message=msg)
