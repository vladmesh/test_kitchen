Тестовое задание (Senior Python): многопользовательская мини-CRM
Цель
Проверить:
    • архитектурное мышление (слои, модули, зависимости),
    • владение современным стеком Python (async, типизация, тесты),
    • умение проектировать API и бизнес-логику под масштабируемый продукт (крупный проект).
Краткое описание
Нужно разработать backend-сервис «мини-CRM» с поддержкой нескольких организаций (multi-tenant):
    • Организации (компании)
    • Пользователи (с ролями в рамках организаций)
    • Контакты
    • Сделки
    • Задачи по сделкам
    • Таймлайн активности по сделке (комментарии/события)
Сервис должен:
    • предоставлять версионированное JSON API (/api/v1/...),
    • работать с PostgreSQL,
    • иметь миграции, тесты, документацию, минимальную авторизацию/роли.
Технологические требования
Обязательно:
    • Python 3.10+
    • Рекомендуемый стек:
    • FastAPI (async)
    • SQLAlchemy / SQLAlchemy Core + Alembic (миграции)
    • PostgreSQL
    • JWT-аутентификация (access/refresh токены)
    • Аннотации типов (type hints), базовая проверка (mypy/pyright – можно сделать конфиг и пару примеров)
Плюсом будет:
    • docker / docker-compose
    • Настройки через pydantic-settings или аналог
    • Разделение на уровни: api / services / repositories / models
    • Простое кэширование (например, in-memory кэш списка статусов сделок или аналитики на N секунд)
Модель данных (расширенная)
Минимум (можно расширять, но не упрощать):
    1. Organization
    • id
    • name
    • created_at
    1. User
    • id
    • email (уникальный)
    • hashed_password
    • name
    • created_at
    1. OrganizationMember
    • id
    • organization_id
    • user_id
    • role (owner, admin, manager, member)
    • уникальность пары (organization_id, user_id)
    1. Contact
    • id
    • organization_id
    • owner_id (User)
    • name
    • email
    • phone
    • created_at
    1. Deal
    • id
    • organization_id
    • contact_id
    • owner_id (User)
    • title
    • amount (decimal)
    • currency (строка, напр. "USD", "EUR")
    • status (new, in_progress, won, lost)
    • stage (этап воронки, напр. qualification, proposal, negotiation, closed)
    • created_at
    • updated_at
    1. Task
    • id
    • deal_id
    • title
    • description
    • due_date
    • is_done
    • created_at
    1. Activity (таймлайн активности по сделке)
    • id
    • deal_id
    • author_id (User, может быть null для системных событий)
    • type (например: comment, status_changed, task_created, system)
    • payload (JSONB с произвольными деталями)
    • created_at
Бизнес-требования и правила
1. Multi-tenant и роли
    • Каждый запрос выполняется от имени авторизованного пользователя.
    • Пользователь может работать только в контексте одной организации за раз (например, через заголовок X-Organization-Id).
    • Проверки прав:
    • owner / admin могут всё внутри организации.
    • manager может управлять всеми сущностями, кроме настроек организации.
    • member может видеть всё, но изменять только:
    • свои контакты,
    • свои сделки,
    • свои задачи.
    • Любая попытка доступа к чужой организации → 403 или 404 (но последовательно).
2. Правила по сделкам и задачам (усложнённые)
    1. Нельзя закрыть сделку со статусом won, если amount <= 0.
    2. Нельзя удалить контакт, если есть сделки в любой стадии.
    3. Нельзя создать задачу для сделки другого пользователя, если роль member.
    4. Нельзя установить due_date в прошлом (минимум «сегодня»).
    5. Переход стадии сделки:
    • По умолчанию запрещён откат стадии назад, кроме ролей admin/owner.
    • Переход стадии вперёд – разрешён, при этом:
    • в таблицу Activity автоматически пишется запись status_changed/stage_changed.
    1. При смене статуса на won:
    • Автоматически создаётся Activity c type="status_changed" и payload с предыдущим и новым статусом.
    1. Организационный контекст:
    • Нельзя привязать контакт, сделку или задачу к сущности из другой организации (например, Deal.organization_id и Contact.organization_id должны совпадать).
3. Аналитика / отчёты
Нужно сделать минимум два аналитических эндпоинта:
    1. Сводка по сделкам (/analytics/deals/summary) для текущей организации:
    • количество сделок по статусам,
    • сумма amount по статусам,
    • средний amount по выигранным (won),
    • количество новых сделок за последние N дней (например, 30).
    1. Воронка продаж (/analytics/deals/funnel):
    • количество сделок по стадиям (stage) в разрезе статусов,
    • конверсия из предыдущей стадии в следующую (в процентах; допустимо считать грубо).
Нефункциональные требования (Senior-уровень)
Архитектура
    • Разделить проект на слои, например:
    • api (роуты, схемы запрос/ответ),
    • services (бизнес-логика),
    • repositories (работа с БД),
    • models (ORM-модели).
    • Не смешивать HTTP-слой и чистые сервисы (сияет, если пригодится для фоновых задач).
Тесты
    • Unit-тесты бизнес-логики (правила перехода статусов, ролей и т.д.).
    • Интеграционные тесты API (через TestClient / httpx):
    • полный сценарий: регистрация → создание организации → добавление участника → создание контакта → сделки → задачи → аналитика.
    • Желательно: использование фикстур для setup/teardown БД.
Качество кода
    • Typed Python (минимум в публичных интерфейсах).
    • Явная обработка ошибок, в т.ч.:
    • 400 – валидационные ошибки,
    • 401 – неавторизовано,
    • 403 – нет прав,
    • 404 – не найдено,
    • 409 – конфликт (например, попытка удалить контакт с активными сделками).
    • Линтер (ruff/flake8/isort – достаточно конфигурации и понятного стиля).
Структура API (пример)
Все пути начинаются с /api/v1.
Аутентификация
POST /api/v1/auth/register
Регистрация пользователя и первой организации (упрощённо).
Request (JSON):
{
  "email": "owner@example.com",
  "password": "StrongPassword123",
  "name": "Alice Owner",
  "organization_name": "Acme Inc"
}

POST /api/v1/auth/login
Request:
{
  "email": "owner@example.com",
  "password": "StrongPassword123"
}


Организации и участники
GET /api/v1/organizations/me
Возвращает список организаций, в которых состоит текущий пользователь.
Контакты
Базовый URL: /api/v1/contacts
GET /api/v1/contacts
Параметры:
    • page (int, default=1)
    • page_size (int, max 100)
    • search (строка по name/email)
    • owner_id (фильтр по владельцу, доступен для manager/admin/owner)
POST /api/v1/contacts
Request:
{
  "name": "John Doe",
  "email": "john.doe@example.com",
  "phone": "+123456789"
}

Сделки
Базовый URL: /api/v1/deals
GET /api/v1/deals
Параметры:
    • page, page_size
    • status (массив: status=new&status=in_progress)
    • min_amount, max_amount
    • stage
    • owner_id (для ролей выше member)
    • сортировка: order_by (например, created_at, amount) и order (asc/desc)

POST /api/v1/deals
Request:
{
  "contact_id": 101,
  "title": "Website redesign",
  "amount": 10000.0,
  "currency": "EUR"
}

PATCH /api/v1/deals/{deal_id}
Частичное обновление (например, изменение статуса/стадии).
Request:
{
  "status": "won",
  "stage": "closed"
}

Валидации:
    • При status="won" → amount > 0, иначе 400.
    • Проверка допустимости перехода stage (без отката для member).

При успешной смене статуса ожидается, что в Activity будет создана запись (см. ниже).
Задачи
Базовый URL: /api/v1/tasks
GET /api/v1/tasks
Параметры:
    • deal_id – фильтр по сделке
    • only_open (bool) – только is_done=false
    • due_before, due_after – фильтр по срокам

POST /api/v1/tasks
Request:
{
  "deal_id": 201,
  "title": "Call client",
  "description": "Discuss proposal details",
  "due_date": "2025-01-15"
}

Валидации:
    • due_date не в прошлом.
    • deal_id принадлежит текущей организации.
    • Для роли member – сделка должна принадлежать этому пользователю.

Активности (таймлайн)
Базовый URL: /api/v1/deals/{deal_id}/activities
GET /api/v1/deals/{deal_id}/activities
POST /api/v1/deals/{deal_id}/activities
Только для type="comment" (бизнес-логика изменения статусов сама создаёт активность).
Request:
{
  "type": "comment",
  "payload": {
    "text": "Client requested updated proposal"
  }
}

Аналитика
GET /api/v1/analytics/deals/summary
Без параметров, работает в рамках текущей организации.
GET /api/v1/analytics/deals/funnel
Формат ошибок (пример)
Рекомендуемый единый формат:

Формат сдачи
    • Repo (GitHub / GitLab) или архив.
    • В репо:
    • исходный код (разбитый по слоям),
    • тесты,
    • README.md с:
    • описанием архитектуры ( коротко ) ,
    • инструкцией запуска,
