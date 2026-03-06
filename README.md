# app-L5x (MVP Scaffold)

Local-first engineering tool scaffold for Rockwell Studio5000 `.L5X` workflows.

## Stack
- Backend: Python + FastAPI
- Frontend: React + TypeScript + Vite
- Offline-only local architecture

## Project Structure
- `backend/` FastAPI API server
- `frontend/` React web UI
- `.planning/` planning artifacts

## Run Locally

### 1) Backend
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 2) Frontend
```bash
cd frontend
npm install
npm run dev
```

Frontend: `http://127.0.0.1:5173`
Backend health: `http://127.0.0.1:8000/api/health`
