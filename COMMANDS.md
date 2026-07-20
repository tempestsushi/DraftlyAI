# Project Commands

## Ollama

Start the local Ollama server:

```powershell
ollama serve
```

Check that the installed model is available:

```powershell
ollama list
```

Run the model directly:

```powershell
ollama run llama3.2:3b
```

## Backend

Move into the backend:

```powershell
cd backend
```

Activate the virtual environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install backend dependencies:

```powershell
python -m pip install -r requirements.txt
```

Run the FastAPI backend:

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 --no-access-log
```

Quick backend import check:

```powershell
python -c "from app.main import app; print(app.title)"
```

## Frontend

Move into the frontend:

```powershell
cd frontend
```

Install frontend dependencies:

```powershell
npm install
```

Run the Vite dev server:

```powershell
npm run dev
```

Build the frontend:

```powershell
npm run build
```

Typecheck the frontend:

```powershell
npm run typecheck
```

## Agent Test Flow

1. Start Ollama:

```powershell
ollama serve
```

2. Start the backend:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 --no-access-log
```

3. Start the frontend:

```powershell
cd frontend
npm run dev
```

4. Open the app in the browser and initialize the agent from the dashboard.
