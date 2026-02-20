# Meetheman API

FastAPI backend implementing university-scoped multi-tenant goal coaching:
- Auth with school domain allowlist + bearer tokens
- Goal catalog, user goals, weekly steps, progress/streak updates
- Mentor listing and match requests
- Auto cohorts and weekly check-ins

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/meetheman
python scripts/init_db.py
uvicorn app.main:app --reload
```

## Docker

```bash
docker compose up --build
```

## Test

```bash
pytest -q
```
