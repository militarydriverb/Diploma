# Shopping Service API

API-бэкенд сервиса покупки товаров для авторизованных пользователей.
Разработан на **FastAPI** + **PostgreSQL** + **SQLAlchemy** (async) + **JWT**.

---

## Стек технологий

| Компонент | Версия |
|---|---|
| Python | 3.14 |
| FastAPI | 0.115 |
| SQLAlchemy | 2.0 (async) |
| asyncpg | 0.31 |
| PostgreSQL | 16 |
| Alembic | 1.15 |
| PyJWT | 2.10 |
| bcrypt | 5.0 |
| Docker / docker-compose | — |

---

## Структура проекта

```
.
├── app/
│   ├── main.py              # Точка входа FastAPI
│   ├── config.py            # Настройки приложения (pydantic-settings)
│   ├── database.py          # Движок и сессия SQLAlchemy
│   ├── models/
│   │   ├── user.py          # Модель пользователя
│   │   ├── product.py       # Модель товара
│   │   └── cart.py          # Модели корзины и позиций
│   ├── schemas/
│   │   ├── user.py          # Pydantic-схемы пользователя
│   │   ├── product.py       # Pydantic-схемы товара
│   │   └── cart.py          # Pydantic-схемы корзины
│   ├── services/
│   │   ├── auth.py          # Бизнес-логика аутентификации
│   │   ├── product.py       # Бизнес-логика товаров
│   │   └── cart.py          # Бизнес-логика корзины
│   ├── routers/
│   │   ├── auth.py          # Эндпоинты /auth
│   │   ├── products.py      # Эндпоинты /products
│   │   └── cart.py          # Эндпоинты /cart
│   └── dependencies/
│       └── auth.py          # Зависимости FastAPI (JWT-проверка)
├── tests/
│   ├── conftest.py          # Фикстуры pytest
│   ├── test_auth.py         # Тесты регистрации и авторизации
│   ├── test_products.py     # Тесты CRUD товаров
│   └── test_cart.py         # Тесты корзины
├── alembic/
│   ├── env.py               # Конфигурация Alembic
│   └── versions/
│       └── 0001_initial.py  # Начальная миграция
├── alembic.ini              # Настройки Alembic
├── docker-compose.yml       # Оркестрация сервисов
├── Dockerfile               # Образ приложения
├── requirements.txt         # Зависимости Python
├── pytest.ini               # Конфигурация pytest
└── .env.example             # Пример переменных окружения
```

---

## Быстрый старт (Docker)

### 1. Клонирование репозитория

```bash
git clone <repo-url>
cd diploma
```

### 2. Настройка переменных окружения

```bash
cp .env.example .env
# Отредактируйте .env при необходимости (SECRET_KEY и т.д.)
```

### 3. Запуск через Docker Compose

```bash
docker-compose up --build
```

После запуска:
- API доступно по адресу: **http://localhost:8000**
- Swagger UI: **http://localhost:8000/docs**
- ReDoc: **http://localhost:8000/redoc**

---

## Запуск без Docker (локальная разработка)

### 1. Создайте виртуальное окружение

```bash
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
.venv\Scripts\activate      # Windows
```

### 2. Установите зависимости

```bash
pip install -r requirements.txt
```

### 3. Настройте переменные окружения

```bash
cp .env.example .env
# Укажите DATABASE_URL для локального PostgreSQL, например:
# DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/diploma
```

### 4. Примените миграции

```bash
alembic upgrade head
```

### 5. Запустите сервер

```bash
uvicorn app.main:app --reload
```

---

## Запуск тестов

Тесты используют отдельную базу данных. Убедитесь, что PostgreSQL запущен и создана БД `diploma_test`.

```sql
CREATE DATABASE diploma_test;
```

```bash
# Запуск с отчётом о покрытии
pytest --cov=app --cov-report=term-missing

# Запуск только тестов аутентификации
pytest tests/test_auth.py -v

# Запуск с подробным выводом
pytest -v
```

**Покрытие кода: 98%** (50 тестов: аутентификация, товары, корзина).

---

## API — Эндпоинты

### Аутентификация (без токена)

| Метод | URL | Описание |
|---|---|---|
| POST | `/auth/register` | Регистрация пользователя |
| POST | `/auth/login` | Вход (email или телефон + пароль) |

### Товары (требуется JWT)

| Метод | URL | Доступ | Описание |
|---|---|---|---|
| GET | `/products/` | Все авторизованные | Список активных товаров |
| GET | `/products/{id}` | Все авторизованные | Получение товара по ID |
| POST | `/products/` | Администратор | Создание товара |
| PATCH | `/products/{id}` | Администратор | Обновление товара |
| DELETE | `/products/{id}` | Администратор | Удаление товара |

### Корзина (требуется JWT)

| Метод | URL | Описание |
|---|---|---|
| GET | `/cart/` | Получить корзину с итоговой суммой |
| POST | `/cart/items` | Добавить один товар |
| POST | `/cart/items/bulk` | Добавить несколько товаров |
| DELETE | `/cart/items` | Удалить товар из корзины |
| DELETE | `/cart/` | Очистить корзину |

---

## Требования к данным

### Пароль
- Не менее 8 символов
- Только латинские буквы, цифры и спецсимволы
- Минимум 1 заглавная буква
- Минимум 1 спецсимвол из набора: `$`, `%`, `&`, `!`, `:`

### Телефон
- Формат: `+7XXXXXXXXXX` (начинается с `+7`, далее 10 цифр)

---

## Безопасность

- Пароли хранятся в виде **bcrypt**-хешей
- Аутентификация через **JWT Bearer Token**
- Неавторизованные запросы возвращают `HTTP 401` с телом `{"code": 401, "message": "Unauthorized"}`
- Административные операции требуют флага `is_admin = true` у пользователя
