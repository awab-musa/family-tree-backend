"""
Simple Role-Based Access Control (RBAC).
Roles: viewer (read-only) / admin (full CRUD).
"""
from enum import Enum

from fastapi import HTTPException, status


class Role(str, Enum):
    VIEWER = "viewer"
    ADMIN = "admin"


def require_admin(role: str) -> None:
    """Raise 403 if the current user's role is not admin. Use inside route handlers
    via the `current_user` dependency, e.g.:

        current_user: TokenPayload = Depends(get_current_user)
        require_admin(current_user.role)
    """
    if role != Role.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required for this action.",
        )
