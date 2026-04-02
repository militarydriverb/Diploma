from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.routers import auth, cart, products

app = FastAPI(
    title="Shopping Service API",
    description="API-бэкенд сервиса покупки товаров для авторизованных пользователей",
    version="1.0.0",
)

# Подключение роутеров
app.include_router(auth.router)
app.include_router(products.router)
app.include_router(cart.router)


@app.exception_handler(401)
async def unauthorized_handler(request: Request, exc):
    """Глобальный обработчик 401 — возвращает стандартный формат ошибки."""
    return JSONResponse(
        status_code=401,
        content={"code": 401, "message": "Unauthorized"},
    )


@app.get("/health", tags=["Служебные"])
async def health_check():
    """Проверка работоспособности сервиса."""
    return {"status": "ok"}
