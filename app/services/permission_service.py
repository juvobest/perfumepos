from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.permission import Permission
from app.models.role import Role
from app.models.user import User
from app.models.associations import (
    user_roles,
    role_permissions,
)


def user_has_permission(
    session: Session,
    user: User,
    permission_name: str,
) -> bool:
    statement = (
        select(Permission.id)
        .select_from(Permission)
        .join(
            role_permissions,
            Permission.id == role_permissions.c.permission_id,
        )
        .join(
            Role,
            Role.id == role_permissions.c.role_id,
        )
        .join(
            user_roles,
            Role.id == user_roles.c.role_id,
        )
        .where(
            user_roles.c.user_id == user.id,
            Permission.name == permission_name,
        )
    )

    return session.scalar(statement) is not None


def require_permission(
    session: Session,
    user: User,
    permission_name: str,
) -> None:
    if not user_has_permission(
        session,
        user,
        permission_name,
    ):
        raise PermissionError(
            f"Permission denied: {permission_name}"
        )