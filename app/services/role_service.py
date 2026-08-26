from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.permission import Permission
from app.models.role import Role


class RoleService:
    def __init__(self, session: Session):
        self.session = session

    # ==========================================================
    # ROLES
    # ==========================================================

    def list_roles(self) -> list[Role]:
        statement = (
            select(Role)
            .order_by(Role.id)
        )

        return list(
            self.session.scalars(statement).all()
        )

    def get_by_id(
        self,
        role_id: int,
    ) -> Role | None:
        return self.session.get(
            Role,
            role_id,
        )

    def get_by_name(
        self,
        name: str,
    ) -> Role | None:
        statement = select(Role).where(
            Role.name == name
        )

        return self.session.scalar(statement)

    def create_role(
        self,
        name: str,
        description: str | None = None,
    ) -> Role:
        name = name.strip()

        if not name:
            raise ValueError(
                "Role name is required."
            )

        if len(name) > 50:
            raise ValueError(
                "Role name cannot exceed 50 characters."
            )

        existing = self.get_by_name(name)

        if existing is not None:
            raise ValueError(
                "Role already exists."
            )

        role = Role(
            name=name,
            description=(
                description.strip()
                if description
                else None
            ),
        )

        self.session.add(role)
        self.session.flush()

        return role

    def update_role(
        self,
        role_id: int,
        name: str | None = None,
        description: str | None = None,
    ) -> Role:
        role = self.get_by_id(role_id)

        if role is None:
            raise ValueError(
                "Role not found."
            )

        if name is not None:
            name = name.strip()

            if not name:
                raise ValueError(
                    "Role name is required."
                )

            if len(name) > 50:
                raise ValueError(
                    "Role name cannot exceed 50 characters."
                )

            existing = self.get_by_name(name)

            if (
                existing is not None
                and existing.id != role.id
            ):
                raise ValueError(
                    "Role already exists."
                )

            role.name = name

        if description is not None:
            description = description.strip()

            role.description = (
                description
                if description
                else None
            )

        self.session.flush()

        return role

    def delete_role(
        self,
        role_id: int,
    ) -> None:
        role = self.get_by_id(role_id)

        if role is None:
            raise ValueError(
                "Role not found."
            )

        if role.name == "Admin":
            raise ValueError(
                "The Admin role cannot be deleted."
            )

        if role.users:
            raise ValueError(
                "Cannot delete a role assigned to users."
            )

        self.session.delete(role)
        self.session.flush()

    # ==========================================================
    # PERMISSIONS
    # ==========================================================

    def list_permissions(
        self,
    ) -> list[Permission]:
        statement = (
            select(Permission)
            .order_by(Permission.id)
        )

        return list(
            self.session.scalars(statement).all()
        )

    def get_role_permissions(
        self,
        role_id: int,
    ) -> list[Permission]:
        role = self.get_by_id(role_id)

        if role is None:
            raise ValueError(
                "Role not found."
            )

        return list(role.permissions)

    def set_permissions(
        self,
        role_id: int,
        permission_ids: list[int],
    ) -> Role:
        role = self.get_by_id(role_id)

        if role is None:
            raise ValueError(
                "Role not found."
            )

        statement = select(Permission).where(
            Permission.id.in_(permission_ids)
        )

        permissions = list(
            self.session.scalars(statement).all()
        )

        if len(permissions) != len(
            set(permission_ids)
        ):
            raise ValueError(
                "One or more permissions were not found."
            )

        role.permissions = permissions

        self.session.flush()

        return role