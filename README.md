# Homework30 LMS API

DRF-проект с курсами, уроками, подписками, Stripe-оплатой, Celery, Redis, PostgreSQL, Gunicorn и Nginx.

## Локальный запуск через Docker Compose

1. Скопируйте переменные окружения:

```bash
cp .env.template .env
```

На Windows PowerShell:

```powershell
copy .env.template .env
```

2. Заполните `.env`: `SECRET_KEY`, `POSTGRES_PASSWORD`, `ALLOWED_HOSTS`, `EXTERNAL_URL`, Stripe/email-переменные.

3. Запустите проект:

```bash
docker compose up --build
```

4. Приложение будет доступно:

```text
http://localhost/
http://localhost/api/docs/
http://localhost/api/schema/
```

## Сервисы Docker Compose

- `nginx` — внешний HTTP-вход, порт `80`.
- `web` — Django + Gunicorn, доступен только внутри Docker-сети через `expose: 8000`.
- `db` — PostgreSQL, доступен только внутри Docker-сети через `expose: 5432`, данные сохраняются в volume `postgres_data`.
- `redis` — брокер Celery, доступен только внутри Docker-сети через `expose: 6379`, данные сохраняются в volume `redis_data`.
- `celery` — Celery worker.
- `celery-beat` — периодические задачи Celery Beat.

## Команды проверки

```bash
docker compose exec web python manage.py check
docker compose exec web python manage.py test
docker compose exec web coverage run manage.py test
docker compose exec web coverage report
```

## Production-сервер

На сервере должны быть установлены:

```bash
sudo apt update
sudo apt install -y docker.io docker-compose-plugin git
sudo systemctl enable --now docker
```

Откройте только нужные порты:

```bash
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

Клонируйте репозиторий:

```bash
git clone <repo-url> homework30
cd homework30
cp .env.template .env
nano .env
docker compose up -d --build
```

## GitHub Actions Secrets

В репозитории GitHub добавьте secrets:

```text
DOCKER_USERNAME
DOCKER_PASSWORD
SERVER_HOST
SERVER_USER
SERVER_SSH_KEY
SERVER_PORT
SERVER_PROJECT_DIR
```

`SERVER_SSH_KEY` — приватный SSH-ключ пользователя, у которого есть доступ к серверу и проекту.

## CI/CD

Workflow `.github/workflows/ci-cd.yml` выполняет этапы:

1. Tests — установка зависимостей, проверка миграций, тесты, coverage.
2. Lint — flake8.
3. Build — сборка и публикация Docker-образа.
4. Deploy — SSH-деплой на сервер после успешного build из ветки `main`.

Ошибки тестов или линтера останавливают pipeline.

## Pull Request

PR оформляйте из ветки домашнего задания в `main`. В PR должны попасть только файлы задания. Не добавляйте в репозиторий `.env`, `.venv`, `db.sqlite3`, `__pycache__`, `htmlcov`, локальные логи и IDE-файлы.
