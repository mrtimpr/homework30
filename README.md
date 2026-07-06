# Homework30 LMS API

Django REST Framework проект для управления курсами, уроками, пользователями, подписками, Stripe-платежами и фоновой рассылкой уведомлений через Celery.

## Стек

- Python 3.14
- Django / Django REST Framework
- PostgreSQL
- Redis
- Celery
- Celery Beat
- drf-spectacular
- Stripe API
- Docker Compose

## Быстрый запуск через Docker Compose

### 1. Подготовить переменные окружения

Скопируйте пример файла окружения:

```bash
cp .env.sample .env
```

Для Windows PowerShell:

```powershell
copy .env.sample .env
```

Проверьте значения в `.env`. Для локального запуска можно оставить значения по умолчанию.

Обязательные переменные для Docker Compose:

```env
SECRET_KEY=django-insecure-change-this-key-for-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
EXTERNAL_URL=http://localhost:8000

POSTGRES_DB=homework30
POSTGRES_USER=homework30
POSTGRES_PASSWORD=homework30_password
POSTGRES_HOST=db
POSTGRES_PORT=5432

REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
DEFAULT_FROM_EMAIL=noreply@example.com

STRIPE_API_KEY=sk_test_change_me
STRIPE_CURRENCY=rub
```

### 2. Запустить проект одной командой

```bash
docker compose up --build
```

Команда поднимет все части проекта:

- `web` — Django API;
- `db` — PostgreSQL;
- `redis` — брокер Celery;
- `celery` — Celery worker;
- `celery-beat` — планировщик периодических задач.

Django автоматически выполнит миграции и запустится на адресе:

```text
http://localhost:8000/
```

Документация API доступна по адресам:

```text
http://localhost:8000/api/schema/
http://localhost:8000/api/docs/
```

### 3. Создать суперпользователя

В отдельном терминале выполните:

```bash
docker compose exec web python manage.py createsuperuser
```

### 4. Загрузить фикстуру группы модераторов

```bash
docker compose exec web python manage.py loaddata groups.json
```

### 5. Запустить тесты

```bash
docker compose exec web python manage.py test
```

Покрытие:

```bash
docker compose exec web coverage run manage.py test
docker compose exec web coverage report > coverage.txt
```

### 6. Остановить проект

```bash
docker compose down
```

Остановить проект и удалить volumes с данными PostgreSQL/Redis:

```bash
docker compose down -v
```

## Сервисы Docker Compose

В `docker-compose.yml` описаны сервисы:

| Сервис | Назначение | Доступ |
|---|---|---|
| `web` | Django API | `ports: 8000:8000` |
| `db` | PostgreSQL | `expose: 5432`, внешний порт не открыт |
| `redis` | Redis | `expose: 6379`, внешний порт не открыт |
| `celery` | Celery worker | внешний порт не нужен |
| `celery-beat` | периодические задачи | внешний порт не нужен |

Для сохранности данных используются volumes:

- `postgres_data` — данные PostgreSQL;
- `redis_data` — данные Redis;
- `static_volume` — собранные static-файлы;
- `media_volume` — media-файлы;
- `celery_beat_data` — служебные файлы Celery Beat.

## Локальный запуск без Docker

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.sample .env
python manage.py migrate
python manage.py runserver
```

Для Windows PowerShell:

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.sample .env
python manage.py migrate
python manage.py runserver
```

Отдельно запустите Redis, затем Celery:

```bash
celery -A config worker -l info
celery -A config beat -l info
```

## Проверка перед Pull Request

```bash
python manage.py check
python manage.py test
```

В PR должны попасть только файлы задания, например:

```text
Dockerfile
docker-compose.yml
.dockerignore
.env.sample
.gitignore
README.md
config/settings.py
requirements.txt
```

Не добавляйте в репозиторий `.env`, `.venv`, `db.sqlite3`, `__pycache__`, `.coverage`, `htmlcov`, `media`, `staticfiles` и служебные файлы IDE.
