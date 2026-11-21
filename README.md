# Macro Tracker

CS348 project — a database-backed macro/calorie tracking web app.

**Stack:** React frontend, FastAPI backend, and MySQL.

The app lets you add, edit, and delete food log entries, then report logged nutrition by date and per-entry calorie range. The food selector is populated from the MySQL `foods` table. The backend creates the tables and seeds the food catalog the first time it connects.

## Running locally

### Backend
```bash
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS macro_tracker CHARACTER SET utf8mb4"
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
export MYSQL_HOST=127.0.0.1
export MYSQL_PORT=3306
export MYSQL_USER=root
export MYSQL_PASSWORD="your actual MySQL root password"
export MYSQL_DATABASE=macro_tracker
python -m uvicorn main:app --reload
```
Replace `root` and the password with the MySQL account you use locally. Do not enter the example phrase literally. To check your credentials, run `mysql -h 127.0.0.1 -u root -p macro_tracker -e "SELECT 1"` and enter the password at the prompt. If your local account has no password, set `MYSQL_PASSWORD=""`. Backend runs at http://localhost:8000.

### Frontend
```bash
cd frontend
npm install
npm run dev
```
Frontend runs at http://localhost:5173

## AI Usage

OpenAI Codex was used only to assist with parts of the React frontend. All backend development and database changes were completed without AI assistance. I reviewed the frontend code to ensure it aligned with the project's requirements and existing functionality. The relevant code and changes are explained in the recorded presentation.