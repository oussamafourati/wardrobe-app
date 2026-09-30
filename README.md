# Wardrobe app

Outfit and makeup suggestions for the occasion you are dressing for.
French first, English second.

## Layout

    apps/mobile        Expo (React Native) app, TypeScript
    apps/api           FastAPI backend (Python 3.13, managed with uv)
    packages/taxonomy  Stable keys and fr/en labels (shared vocabulary)
    evals              Golden cases and data checks
    infra              docker-compose for Postgres 17 + pgvector

## Prerequisites (Windows)

- Node.js 22.13 or newer (24 LTS recommended)
- Git
- uv (winget install --id astral-sh.uv -e)
- Docker Desktop
- Expo Go on an Android phone, on the same Wi-Fi as the PC

## First-time setup

    npm install
    Copy-Item apps\api\.env.example apps\api\.env
    Copy-Item apps\mobile\.env.example apps\mobile\.env
    docker compose -f infra\docker-compose.yml up -d

Then edit apps\mobile\.env and put your PC's Wi-Fi address in
EXPO_PUBLIC_API_URL (for example http://192.168.1.20:8000).

## Run

    cd apps\api ; uv run fastapi dev main.py --host 0.0.0.0
    cd apps\mobile ; npx expo start -c

Open Expo Go on the phone and scan the QR code.

## Checks (the same ones CI runs)

    cd apps\api ; uv run pytest -v
    cd apps\mobile ; npx tsc --noEmit
    uv run --no-project --python 3.13 evals/check_data.py

## Rules

- Never commit .env files. The local database password is for development only.
- One branch per story, merged through a pull request with green CI.

## Database migrations

    cd apps\api ; uv run alembic upgrade head
    cd apps\api ; uv run alembic revision --autogenerate -m "describe the change"
    cd apps\api ; uv run alembic check

Change models.py first, generate a migration, and read the generated file
before committing it. CI applies the migrations on a blank database and
runs alembic check to catch any drift between models and migrations.
