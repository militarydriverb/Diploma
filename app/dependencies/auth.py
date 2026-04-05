import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.services.auth import decode_access_token, get_user_by_id

# Схема Bearer-аутентификации (auto_error=False — обрабатываем отсутствие токена вручную)
bearer_scheme = HTTPBearer(auto_error=False)

# Стандартная ошибка 401 согласно ТЗ
UNAUTHORIZED = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail={"code": 401, "message": "Unauthorized"},
)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Зависимость: возвращает текущего авторизованного пользователя.
    Вызывает 401, если токен отсутствует, невалиден или пользователь неактивен.
    """
    if not credentials:
        raise UNAUTHORIZED
    try:
        payload = decode_access_token(credentials.credentials)
        user_id: int = payload.get("sub")
        if user_id is None:
            raise UNAUTHORIZED
    except jwt.PyJWTError:
        raise UNAUTHORIZED

    user = await get_user_by_id(db, int(user_id))
    if not user or not user.is_active:
        raise UNAUTHORIZED
    return user


async def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Зависимость: возвращает текущего пользователя только если он администратор.
    Вызывает 403, если пользователь не является администратором.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": 403,
                "message": "Forbidden: требуются права администратора",
            },
        )
    return current_user
