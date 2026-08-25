# Macro Tracker

CS348 project — a database-backed macro/calorie tracking web app.

**Stack:** React (Vite) frontend, FastAPI backend, MySQL database (added in later stages).

## Stage 1 status
Hello world running end-to-end: React frontend fetches a message from the FastAPI backend.

## Running locally

### Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate       # on Windows: venv\Scripts\activate
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
