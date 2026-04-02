from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.user import TokenResponse, UserRegister, UserLogin, UserResponse
from app.services.auth import authenticate_user, create_access_token, register_user

router = APIRouter(prefix="/auth", tags=["Аутентификация"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)):
    """Регистрация нового пользователя. Доступно без аутентификации."""
    try:
        user = await register_user(db, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return user


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    """Вход по email или телефону. Возвращает JWT-токен. Доступно без аутентификации."""
    user = await authenticate_user(db, data.login, data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": 401, "message": "Unauthorized"},
        )
    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token)
