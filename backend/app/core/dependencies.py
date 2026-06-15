from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DomainError
from app.core.logging import user_id_var
from app.core.security import parse_user_id_from_token
from app.database import get_db

security = HTTPBearer(auto_error=False)


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> UUID:
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "AUTHENTICATION_ERROR", "message": "Missing authentication token"},
        )
    try:
        user_id = parse_user_id_from_token(credentials.credentials)
        user_id_var.set(str(user_id))
        return user_id
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "AUTHENTICATION_ERROR", "message": "Invalid or expired token"},
        ) from exc


async def get_session(db: AsyncSession = Depends(get_db)) -> AsyncSession:
    return db
