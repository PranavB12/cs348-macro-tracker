# Macro Tracker

CS348 project — a database-backed macro/calorie tracking web app.

**Stack:** React frontend, FastAPI backend, SQLite database for the Stage 2 demo. The relational schema is documented in `docs/stage2-deliverables.md` and maps directly to MySQL.

## Stage 2 workflow
The app lets you add, edit, and delete food log entries, then report logged nutrition by date and per-entry calorie range. The food selector is populated from the `foods` database table. The backend creates `backend/macro_tracker.db` and seeds the food catalog the first time it starts.

The database design and an approximately 8-minute demo script are in [docs/stage2-deliverables.md](docs/stage2-deliverables.md). Stage 1 covered stack setup and a Hello World page; Stage 2 adds the CRUD, report, and database-driven selector demonstrations.

## Running locally

### Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate      
pip install -r requirements.txt
uvicorn main:app --reload
```
Backend runs at http://localhost:8000

### Frontend
```bash
cd frontend
npm install
npm run dev
```
Frontend runs at http://localhost:5173
