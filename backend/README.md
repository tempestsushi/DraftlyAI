# Backend

Local FastAPI backend for Draftly.

## Run

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 --no-access-log
```

## Test

```powershell
cd backend
.venv\Scripts\Activate.ps1
pytest
```

## Endpoints

- `GET /api/health`
- `GET /api/topics`
- `GET /api/drafts`
- `GET /api/repositories`
- `GET /api/integrations`
- `GET /api/agent/stream?topic=...`
- `POST /api/github/sync`
- `POST /api/webhooks/portfolio`
- `POST /api/linkedin/publish`
