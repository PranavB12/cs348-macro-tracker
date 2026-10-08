# Macro Tracker

CS348 project — a database-backed macro/calorie tracking web app.

**Stack:** React frontend, FastAPI backend, and MySQL.

## Stage 2 workflow
The app lets you add, edit, and delete food log entries, then report logged nutrition by date and per-entry calorie range. The food selector is populated from the MySQL `foods` table. The backend creates the tables and seeds the food catalog the first time it connects.

The database design and an approximately 8-minute demo script are in [docs/stage2-deliverables.md](docs/stage2-deliverables.md). Stage 1 covered stack setup and a Hello World page; Stage 2 adds the CRUD, report, and database-driven selector demonstrations.

## Running locally

### Backend
```bash
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS macro_tracker CHARACTER SET utf8mb4"
cd backend
python3 -m venv venv
source venv/bin/activate      
pip install -r requirements.txt
export MYSQL_HOST=127.0.0.1
export MYSQL_PORT=3306
export MYSQL_USER=root
export MYSQL_PASSWORD="your-mysql-password"
export MYSQL_DATABASE=macro_tracker
uvicorn main:app --reload
```
Replace `root` and the password with the MySQL account you use locally. If that account has no password, set `MYSQL_PASSWORD=""`. Backend runs at http://localhost:8000.

### Frontend
```bash
cd frontend
npm install
npm run dev
```
Frontend runs at http://localhost:5173
