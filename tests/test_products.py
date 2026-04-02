import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product

pytestmark = pytest.mark.asyncio


async def create_product(db: AsyncSession, name: str = "Товар", price: int = 100, is_active: bool = True) -> Product:
    """Вспомогательная функция создания товара напрямую в БД."""
    product = Product(name=name, price=price, is_active=is_active)
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product


# ---------------------------------------------------------------------------
# Получение списка товаров
# ---------------------------------------------------------------------------

class TestListProducts:
    async def test_list_products_authorized(self, client: AsyncClient, user_token: str, db_session: AsyncSession):
        """Авторизованный пользователь получает список активных товаров."""
        await create_product(db_session, "Телефон", 50000)
        await create_product(db_session, "Ноутбук", 80000)
        await create_product(db_session, "Скрытый", 1000, is_active=False)

        resp = await client.get("/products/", headers={"Authorization": f"Bearer {user_token}"})
        assert resp.status_code == 200
        data = resp.json()
        # Неактивный товар не должен попасть в список
        assert len(data) == 2
        names = [p["name"] for p in data]
        assert "Скрытый" not in names

    async def test_list_products_unauthorized(self, client: AsyncClient):
        """Неавторизованный запрос возвращает 401."""
        resp = await client.get("/products/")
        assert resp.status_code == 401

    async def test_get_product_by_id(self, client: AsyncClient, user_token: str, db_session: AsyncSession):
        """Получение конкретного товара по ID."""
        product = await create_product(db_session, "Планшет", 30000)
        resp = await client.get(
            f"/products/{product.id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Планшет"

    async def test_get_product_not_found(self, client: AsyncClient, user_token: str):
        """Запрос несуществующего товара возвращает 404."""
        resp = await client.get("/products/99999", headers={"Authorization": f"Bearer {user_token}"})
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Создание товара (только администратор)
# ---------------------------------------------------------------------------

class TestCreateProduct:
    async def test_create_product_as_admin(self, client: AsyncClient, admin_token: str):
        """Администратор может создать товар."""
        payload = {"name": "Наушники", "price": 5000, "is_active": True}
        resp = await client.post("/products/", json=payload, headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Наушники"
        assert data["price"] == 5000
        assert data["is_active"] is True

    async def test_create_product_as_regular_user(self, client: AsyncClient, user_token: str):
        """Обычный пользователь не может создать товар — 403."""
        payload = {"name": "Попытка", "price": 1}
        resp = await client.post("/products/", json=payload, headers={"Authorization": f"Bearer {user_token}"})
        assert resp.status_code == 403

    async def test_create_product_unauthorized(self, client: AsyncClient):
        """Неавторизованный запрос на создание товара — 401."""
        resp = await client.post("/products/", json={"name": "X", "price": 1})
        assert resp.status_code == 401

    async def test_create_product_negative_price(self, client: AsyncClient, admin_token: str):
        """Отрицательная цена отклоняется с 422."""
        payload = {"name": "Плохой товар", "price": -100}
        resp = await client.post("/products/", json=payload, headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Редактирование товара (только администратор)
# ---------------------------------------------------------------------------

class TestUpdateProduct:
    async def test_update_product_as_admin(self, client: AsyncClient, admin_token: str, db_session: AsyncSession):
        """Администратор может отредактировать товар."""
        product = await create_product(db_session, "Старое название", 100)
        resp = await client.patch(
            f"/products/{product.id}",
            json={"name": "Новое название", "price": 200},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Новое название"
        assert data["price"] == 200

    async def test_update_product_not_found(self, client: AsyncClient, admin_token: str):
        """Редактирование несуществующего товара — 404."""
        resp = await client.patch(
            "/products/99999",
            json={"name": "X"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 404

    async def test_update_product_as_regular_user(self, client: AsyncClient, user_token: str, db_session: AsyncSession):
        """Обычный пользователь не может редактировать товар — 403."""
        product = await create_product(db_session)
        resp = await client.patch(
            f"/products/{product.id}",
            json={"price": 1},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Удаление товара (только администратор)
# ---------------------------------------------------------------------------

class TestDeleteProduct:
    async def test_delete_product_as_admin(self, client: AsyncClient, admin_token: str, db_session: AsyncSession):
        """Администратор может удалить товар."""
        product = await create_product(db_session)
        resp = await client.delete(
            f"/products/{product.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 204

    async def test_delete_product_not_found(self, client: AsyncClient, admin_token: str):
        """Удаление несуществующего товара — 404."""
        resp = await client.delete("/products/99999", headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 404

    async def test_delete_product_as_regular_user(self, client: AsyncClient, user_token: str, db_session: AsyncSession):
        """Обычный пользователь не может удалить товар — 403."""
        product = await create_product(db_session)
        resp = await client.delete(
            f"/products/{product.id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 403
