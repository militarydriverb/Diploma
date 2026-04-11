import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------------
# Регистрация
# ---------------------------------------------------------------------------


class TestRegister:
    async def test_register_success(self, client: AsyncClient):
        """Успешная регистрация нового пользователя."""
        payload = {
            "full_name": "Сидоров Сидор Сидорович",
            "email": "sidorov@example.com",
            "phone": "+71112223344",
            "password": "Secret!1",
            "confirm_password": "Secret!1",
        }
        resp = await client.post("/auth/register", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == "sidorov@example.com"
        assert data["phone"] == "+71112223344"
        assert "hashed_password" not in data

    async def test_register_duplicate_email(self, client: AsyncClient, regular_user):
        """Регистрация с уже существующим email возвращает 400."""
        payload = {
            "full_name": "Другой Пользователь",
            "email": "test@example.com",  # уже занят regular_user
            "phone": "+70000000001",
            "password": "Secret!1",
            "confirm_password": "Secret!1",
        }
        resp = await client.post("/auth/register", json=payload)
        assert resp.status_code == 400
        assert "email" in resp.json()["detail"].lower()

    async def test_register_duplicate_phone(self, client: AsyncClient, regular_user):
        """Регистрация с уже существующим телефоном возвращает 400."""
        payload = {
            "full_name": "Другой Пользователь",
            "email": "other@example.com",
            "phone": "+71234567890",  # уже занят regular_user
            "password": "Secret!1",
            "confirm_password": "Secret!1",
        }
        resp = await client.post("/auth/register", json=payload)
        assert resp.status_code == 400

    async def test_register_passwords_mismatch(self, client: AsyncClient):
        """Несовпадение паролей при регистрации возвращает 422."""
        payload = {
            "full_name": "Пользователь",
            "email": "user2@example.com",
            "phone": "+70000000002",
            "password": "Secret!1",
            "confirm_password": "Different!2",
        }
        resp = await client.post("/auth/register", json=payload)
        assert resp.status_code == 422

    @pytest.mark.parametrize(
        "password",
        [
            "short!A",  # меньше 8 символов
            "nouppercase!1",  # нет заглавной буквы
            "NOSPECIAL1A",  # нет спецсимвола
            "НеЛатиница!1A",  # не латиница
            "NoSpecial1",  # нет спецсимвола
        ],
    )
    async def test_register_invalid_password(self, client: AsyncClient, password: str):
        """Невалидный пароль отклоняется с кодом 422."""
        payload = {
            "full_name": "Пользователь",
            "email": "user3@example.com",
            "phone": "+70000000003",
            "password": password,
            "confirm_password": password,
        }
        resp = await client.post("/auth/register", json=payload)
        assert resp.status_code == 422

    @pytest.mark.parametrize(
        "phone",
        [
            "89001234567",  # без +7
            "+7900123456",  # только 9 цифр
            "+79001234567x",  # лишний символ
            "+89001234567",  # начинается с +8
            "7900123456",  # без +
        ],
    )
    async def test_register_invalid_phone(self, client: AsyncClient, phone: str):
        """Невалидный телефон отклоняется с кодом 422."""
        payload = {
            "full_name": "Пользователь",
            "email": "user4@example.com",
            "phone": phone,
            "password": "Secret!1A",
            "confirm_password": "Secret!1A",
        }
        resp = await client.post("/auth/register", json=payload)
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Авторизация
# ---------------------------------------------------------------------------


class TestLogin:
    async def test_login_by_email(self, client: AsyncClient, regular_user):
        """Успешный вход по email возвращает JWT-токен."""
        resp = await client.post(
            "/auth/login", json={"login": "test@example.com", "password": "Password!1"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_by_phone(self, client: AsyncClient, regular_user):
        """Успешный вход по номеру телефона возвращает JWT-токен."""
        resp = await client.post(
            "/auth/login", json={"login": "+71234567890", "password": "Password!1"}
        )
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    async def test_login_wrong_password(self, client: AsyncClient, regular_user):
        """Неверный пароль возвращает 401."""
        resp = await client.post(
            "/auth/login", json={"login": "test@example.com", "password": "WrongPass!1"}
        )
        assert resp.status_code == 401
        assert resp.json()["code"] == 401

    async def test_login_unknown_user(self, client: AsyncClient):
        """Несуществующий пользователь возвращает 401."""
        resp = await client.post(
            "/auth/login", json={"login": "nobody@example.com", "password": "Secret!1"}
        )
        assert resp.status_code == 401

    async def test_unauthorized_access_without_token(self, client: AsyncClient):
        """Запрос без токена возвращает 401 с нужным телом."""
        resp = await client.get("/products/")
        assert resp.status_code == 401
        body = resp.json()
        assert body["code"] == 401
        assert body["message"] == "Unauthorized"

    async def test_unauthorized_access_with_invalid_token(self, client: AsyncClient):
        """Запрос с невалидным токеном возвращает 401."""
        resp = await client.get(
            "/products/", headers={"Authorization": "Bearer invalid.token.here"}
        )
        assert resp.status_code == 401
