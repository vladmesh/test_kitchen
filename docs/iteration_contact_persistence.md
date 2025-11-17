# Итерация: перенести модуль контактов на PostgreSQL

## Контекст
- В `mini_crm.modules.contacts.api.router`/`services` сейчас используется `InMemoryContactRepository`, из-за чего API не сохраняет данные и не удовлетворяет multi-tenant требованиям из `TZ.md`.
- Таблицы и ORM-модель `Contact` уже есть в `migrations/0001_initial.py` и `modules/contacts/models.py`, поэтому можно ограничиться слоем репозитория и DI.
- В проекте нет зависимости, которая выдаёт `AsyncSession` внутрь обработчиков, поэтому сервисы не могут использовать реальную БД.

## Цель
Сделать так, чтобы `/api/v1/contacts` читали и записывали данные в PostgreSQL с учётом `organization_id`, сохранив существующий API и минимально меняя уже работающий код.

## Объём
1. Добавить DI для `AsyncSession`.
2. Реализовать `SQLAlchemyContactRepository`, который покрывает `list` и `create`.
3. Провести замену зависимостей в роутере/сервисе.
4. Написать интеграционный тест, который прогоняет `create` + `list` против тестовой БД.

## План
1. **DB-сессия как зависимость**
   - В `mini_crm.core.dependencies` добавить `async def get_db_session() -> AsyncIterator[AsyncSession]`, который вызывает `mini_crm.core.db.get_session()`.
   - Убедиться, что зависимость корректно закрывает сессию через `async with`.
2. **Репозиторий**
   - Создать `mini_crm/modules/contacts/repositories/sqlalchemy.py`.
   - Класс `SQLAlchemyContactRepository(AbstractContactRepository)` принимает `AsyncSession`.
   - `list()`:
     - `stmt = select(Contact).where(Contact.organization_id == organization_id).order_by(Contact.id).offset((page-1)*page_size).limit(page_size)`.
     - Считать `total` отдельным `select(func.count())` с теми же фильтрами.
     - Конвертировать ORM -> DTO при помощи `ContactResponse.model_validate`.
   - `create()`:
     - Собрать ORM-объект `Contact`, задать `organization_id` и `owner_id`.
     - `session.add`, `await session.flush()`, `await session.refresh(contact)`, вернуть DTO.
   - Добавить файл в `__all__` (если нужно) и обновить `repositories/__init__.py` при его наличии.
3. **Интеграция в сервис**
   - В `api/router.py` заменить глобальный `InMemoryContactRepository`.
   - Добавить зависимость `get_contact_repository(session=Depends(get_db_session)) -> SQLAlchemyContactRepository`.
   - `get_contact_service` теперь принимает репозиторий и возвращает новый `ContactService(repository=repository)`, избегая глобальных синглтонов.
   - Убедиться, что `ContactService` не кэширует репозиторий между запросами.
4. **Тесты**
   - Добавить фикстуру `async_engine` в `services/backend/tests/conftest.py`, которая создаёт `sqlite+aiosqlite:///:memory:` или `postgresql+asyncpg://` (если уже есть контейнер) и прогоняет `Base.metadata.create_all`.
   - Написать `pytest.mark.asyncio` тест, который:
     1. Создаёт `AsyncSession`.
     2. Инициализирует `SQLAlchemyContactRepository`.
     3. Вызывает `create`.
     4. Вызывает `list` и проверяет `total == 1`, `items[0].name == ...`, `organization_id` фильтрацию.
   - Для API-теста использовать `TestClient` + monkeypatch зависимости `get_db_session`, чтобы прокинуть тестовую сессию (через `dependency_overrides`).
5. **Проверка**
   - Локально выполнить `alembic upgrade head` (контейнер или dev DB) — убедиться, что схемы соответствуют.
   - Прогнать `pytest -k contacts` и `ruff check` на изменённые файлы.

## Риски и ограничения
- Потенциальный рост времени тестов при работе с реальной Postgres: если это критично, тестовую сессию можно строить на `sqlite+aiosqlite`.
- Нужно следить за тем, чтобы `get_db_session` не создавал новый движок на каждый запрос (использовать уже существующий `get_session_factory`).
- Перенос только контактов; остальные модули всё ещё используют in-memory слой, это осознанное ограничение текущей итерации.

## Готовый результат
- `/api/v1/contacts` опирается на PostgreSQL и уважает `organization_id`.
- Появились тесты, гарантирующие, что репозиторий корректно работает поверх SQLAlchemy.
- В дальнейшем аналогичный шаблон можно применить к сделкам/задачам.

