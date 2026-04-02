import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product

pytestmark = pytest.mark.asyncio


async def create_product(db: AsyncSession, name: str = "Товар", price: int = 100) -> Product:
    """Вспомогательная функция создания активного товара."""
    product = Product(name=name, price=price, is_active=True)
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product


# ---------------------------------------------------------------------------
# Получение корзины
# ---------------------------------------------------------------------------

class TestGetCart:
    async def test_get_empty_cart(self, client: AsyncClient, user_token: str):
        """Первый запрос корзины создаёт пустую корзину."""
        resp = await client.get("/cart/", headers={"Authorization": f"Bearer {user_token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["total_price"] == 0

    async def test_get_cart_unauthorized(self, client: AsyncClient):
        """Неавторизованный доступ к корзине — 401."""
        resp = await client.get("/cart/")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Добавление товаров в корзину
# ---------------------------------------------------------------------------

class TestAddToCart:
    async def test_add_single_item(self, client: AsyncClient, user_token: str, db_session: AsyncSession):
        """Добавление одного товара в корзину."""
        product = await create_product(db_session, "Книга", 500)

        resp = await client.post(
            "/cart/items",
            json={"product_id": product.id, "quantity": 2},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["product_id"] == product.id
        assert data["items"][0]["quantity"] == 2
        # Итоговая стоимость: 500 * 2 = 1000
        assert data["total_price"] == 1000

    async def test_add_multiple_items_bulk(self, client: AsyncClient, user_token: str, db_session: AsyncSession):
        """Добавление нескольких товаров одним запросом (bulk)."""
        p1 = await create_product(db_session, "Ручка", 50)
        p2 = await create_product(db_session, "Тетрадь", 80)

        resp = await client.post(
            "/cart/items/bulk",
            json={"items": [
                {"product_id": p1.id, "quantity": 3},
                {"product_id": p2.id, "quantity": 1},
            ]},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 2
        # Итого: 50*3 + 80*1 = 230
        assert data["total_price"] == 230

    async def test_add_same_item_increases_quantity(
        self, client: AsyncClient, user_token: str, db_session: AsyncSession
    ):
        """Повторное добавление того же товара увеличивает количество."""
        product = await create_product(db_session, "Карандаш", 30)
        headers = {"Authorization": f"Bearer {user_token}"}

        await client.post("/cart/items", json={"product_id": product.id, "quantity": 1}, headers=headers)
        resp = await client.post("/cart/items", json={"product_id": product.id, "quantity": 2}, headers=headers)

        data = resp.json()
        assert data["items"][0]["quantity"] == 3
        assert data["total_price"] == 90  # 30 * 3

    async def test_add_inactive_product(self, client: AsyncClient, user_token: str, db_session: AsyncSession):
        """Добавление неактивного товара возвращает 404."""
        inactive = Product(name="Снятый товар", price=100, is_active=False)
        db_session.add(inactive)
        await db_session.commit()
        await db_session.refresh(inactive)

        resp = await client.post(
            "/cart/items",
            json={"product_id": inactive.id, "quantity": 1},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 404

    async def test_add_nonexistent_product(self, client: AsyncClient, user_token: str):
        """Добавление несуществующего товара возвращает 404."""
        resp = await client.post(
            "/cart/items",
            json={"product_id": 99999, "quantity": 1},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 404

    async def test_add_item_invalid_quantity(self, client: AsyncClient, user_token: str, db_session: AsyncSession):
        """Количество 0 или отрицательное отклоняется с 422."""
        product = await create_product(db_session)
        resp = await client.post(
            "/cart/items",
            json={"product_id": product.id, "quantity": 0},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 422

    async def test_add_item_unauthorized(self, client: AsyncClient):
        """Добавление товара без авторизации — 401."""
        resp = await client.post("/cart/items", json={"product_id": 1, "quantity": 1})
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Удаление товара из корзины
# ---------------------------------------------------------------------------

class TestRemoveFromCart:
    async def test_remove_item(self, client: AsyncClient, user_token: str, db_session: AsyncSession):
        """Успешное удаление товара из корзины."""
        product = await create_product(db_session, "Линейка", 40)
        headers = {"Authorization": f"Bearer {user_token}"}

        # Сначала добавляем
        await client.post("/cart/items", json={"product_id": product.id, "quantity": 1}, headers=headers)

        # Затем удаляем
        resp = await client.request(
            "DELETE",
            "/cart/items",
            json={"product_id": product.id},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["items"] == []
        assert resp.json()["total_price"] == 0

    async def test_remove_nonexistent_item(self, client: AsyncClient, user_token: str):
        """Удаление товара, которого нет в корзине — 404."""
        resp = await client.request(
            "DELETE",
            "/cart/items",
            json={"product_id": 99999},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 404

    async def test_remove_item_unauthorized(self, client: AsyncClient):
        """Удаление без авторизации — 401."""
        resp = await client.request("DELETE", "/cart/items", json={"product_id": 1})
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Очистка корзины
# ---------------------------------------------------------------------------

class TestClearCart:
    async def test_clear_cart(self, client: AsyncClient, user_token: str, db_session: AsyncSession):
        """Очистка корзины удаляет все товары."""
        p1 = await create_product(db_session, "Товар 1", 100)
        p2 = await create_product(db_session, "Товар 2", 200)
        headers = {"Authorization": f"Bearer {user_token}"}

        await client.post("/cart/items/bulk", json={"items": [
            {"product_id": p1.id, "quantity": 1},
            {"product_id": p2.id, "quantity": 1},
        ]}, headers=headers)

        resp = await client.delete("/cart/", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["total_price"] == 0

    async def test_clear_empty_cart(self, client: AsyncClient, user_token: str):
        """Очистка уже пустой корзины — успех."""
        resp = await client.delete("/cart/", headers={"Authorization": f"Bearer {user_token}"})
        assert resp.status_code == 200
        assert resp.json()["items"] == []

    async def test_clear_cart_unauthorized(self, client: AsyncClient):
        """Очистка без авторизации — 401."""
        resp = await client.delete("/cart/")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Общая стоимость
# ---------------------------------------------------------------------------

class TestCartTotal:
    async def test_total_price_calculation(self, client: AsyncClient, user_token: str, db_session: AsyncSession):
        """Проверка расчёта общей стоимости корзины."""
        p1 = await create_product(db_session, "Товар A", 150)
        p2 = await create_product(db_session, "Товар B", 250)
        headers = {"Authorization": f"Bearer {user_token}"}

        await client.post("/cart/items/bulk", json={"items": [
            {"product_id": p1.id, "quantity": 2},  # 150*2 = 300
            {"product_id": p2.id, "quantity": 3},  # 250*3 = 750
        ]}, headers=headers)

        resp = await client.get("/cart/", headers=headers)
        assert resp.json()["total_price"] == 1050  # 300 + 750
