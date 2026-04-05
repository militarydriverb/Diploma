from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.openapi.docs import get_redoc_html
from fastapi.responses import HTMLResponse, JSONResponse

_INDEX_HTML = (Path(__file__).parent / "templates" / "index.html").read_text(encoding="utf-8")

from app.routers import auth, cart, products

app = FastAPI(
    title="Shopping Service API",
    description="API-бэкенд сервиса покупки товаров для авторизованных пользователей",
    version="1.0.0",
    redoc_url=None,  # отключаем дефолтный ReDoc, заменяем своим ниже
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


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def root():
    """Стартовая страница сервиса."""
    return _INDEX_HTML


@app.get("/redoc", response_class=HTMLResponse, include_in_schema=False)
async def redoc():
    """ReDoc — документация API (JS грузится с unpkg.com)."""
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=app.title + " — ReDoc",
        redoc_js_url="https://unpkg.com/redoc/bundles/redoc.standalone.js",
    )


@app.get("/health", tags=["Служебные"])
async def health_check():
    """Проверка работоспособности сервиса."""
    return {"status": "ok"}
