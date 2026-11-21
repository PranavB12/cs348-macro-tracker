import os
from contextlib import contextmanager
from datetime import date

import pymysql
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


DATABASE_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "127.0.0.1"),
    "port": int(os.getenv("MYSQL_PORT", "3306")),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", ""),
    "database": os.getenv("MYSQL_DATABASE", "macro_tracker"),
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,
    "autocommit": False,
    # Make concurrent report reads see committed data while writers serialize
    # changes to the same entry through InnoDB row locks.
    "init_command": "SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED",
}
SEED_FOODS = [
    ("Oats", 150, 5.0, 27.0, 3.0),
    ("Greek yogurt", 100, 17.0, 6.0, 0.0),
    ("Banana", 105, 1.3, 27.0, 0.4),
    ("Chicken breast", 165, 31.0, 0.0, 3.6),
    ("Brown rice", 216, 5.0, 45.0, 1.8),
    ("Avocado", 160, 2.0, 9.0, 14.7),
]


class Database:
    def __init__(self, connection):
        self.connection = connection

    def execute(self, sql, params=()):
        cursor = self.connection.cursor()
        cursor.execute(sql, params)
        return cursor

    def executemany(self, sql, params):
        cursor = self.connection.cursor()
        cursor.executemany(sql, params)
        return cursor

    def commit(self):
        self.connection.commit()

    @contextmanager
    def transaction(self):
        """Commit a complete write or roll the whole operation back."""
        self.connection.begin()
        try:
            yield
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise


@contextmanager
def connect():
    connection = pymysql.connect(**DATABASE_CONFIG)
    try:
        yield Database(connection)
    finally:
        connection.close()


def initialize_database():
    with connect() as db:
        db.execute(
            """CREATE TABLE IF NOT EXISTS foods (
                id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(120) NOT NULL UNIQUE,
                calories DECIMAL(10,2) NOT NULL CHECK (calories >= 0),
                protein_g DECIMAL(10,2) NOT NULL CHECK (protein_g >= 0),
                carbs_g DECIMAL(10,2) NOT NULL CHECK (carbs_g >= 0),
                fat_g DECIMAL(10,2) NOT NULL CHECK (fat_g >= 0)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"""
        )
        db.execute(
            """CREATE TABLE IF NOT EXISTS food_entries (
                id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                food_id INT NOT NULL,
                entry_date DATE NOT NULL,
                servings DECIMAL(8,2) NOT NULL CHECK (servings > 0),
                calories DECIMAL(10,2) NOT NULL CHECK (calories >= 0),
                protein_g DECIMAL(10,2) NOT NULL CHECK (protein_g >= 0),
                carbs_g DECIMAL(10,2) NOT NULL CHECK (carbs_g >= 0),
                fat_g DECIMAL(10,2) NOT NULL CHECK (fat_g >= 0),
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT fk_food_entries_food FOREIGN KEY (food_id) REFERENCES foods(id),
                INDEX idx_food_entries_date (entry_date),
                INDEX idx_food_entries_date_calories (entry_date, calories)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"""
        )
        # CREATE TABLE IF NOT EXISTS does not change tables already created by
        # Stage 2, so add the reporting index there as an idempotent migration.
        existing_indexes = db.execute("SHOW INDEX FROM food_entries").fetchall()
        if not any(index["Key_name"] == "idx_food_entries_date_calories" for index in existing_indexes):
            db.execute("CREATE INDEX idx_food_entries_date_calories ON food_entries (entry_date, calories)")
        if db.execute("SELECT COUNT(*) AS count FROM foods").fetchone()["count"] == 0:
            db.executemany(
                "INSERT INTO foods (name, calories, protein_g, carbs_g, fat_g) VALUES (%s, %s, %s, %s, %s)",
                SEED_FOODS,
            )
        db.commit()


class EntryInput(BaseModel):
    food_id: int
    entry_date: date
    servings: float = Field(gt=0, le=100)


app = FastAPI(title="Macro Tracker API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    initialize_database()


@app.get("/")
def hello_world():
    return {"message": "Macro Tracker API is ready"}


@app.get("/api/foods")
def list_foods():
    with connect() as db:
        return db.execute("SELECT * FROM foods ORDER BY name").fetchall()


def entry_values(db, payload: EntryInput):
    food = db.execute("SELECT * FROM foods WHERE id = %s", (payload.food_id,)).fetchone()
    if food is None:
        raise HTTPException(status_code=404, detail="Food not found")
    servings = payload.servings
    return (
        payload.food_id,
        payload.entry_date.isoformat(),
        servings,
        *(round(float(food[key]) * servings, 2) for key in ("calories", "protein_g", "carbs_g", "fat_g")),
    )


@app.post("/api/entries", status_code=201)
def create_entry(payload: EntryInput):
    with connect() as db:
        with db.transaction():
            values = entry_values(db, payload)
            cursor = db.execute(
                "INSERT INTO food_entries (food_id, entry_date, servings, calories, protein_g, carbs_g, fat_g) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)", values
            )
            entry_id = cursor.lastrowid
            return db.execute("SELECT * FROM food_entries WHERE id = %s", (entry_id,)).fetchone()


@app.put("/api/entries/{entry_id}")
def update_entry(entry_id: int, payload: EntryInput):
    with connect() as db:
        with db.transaction():
            if db.execute("SELECT id FROM food_entries WHERE id = %s", (entry_id,)).fetchone() is None:
                raise HTTPException(status_code=404, detail="Entry not found")
            values = entry_values(db, payload)
            db.execute(
                "UPDATE food_entries SET food_id = %s, entry_date = %s, servings = %s, calories = %s, "
                "protein_g = %s, carbs_g = %s, fat_g = %s WHERE id = %s",
                (*values, entry_id),
            )
            return db.execute("SELECT * FROM food_entries WHERE id = %s", (entry_id,)).fetchone()


@app.delete("/api/entries/{entry_id}", status_code=204)
def delete_entry(entry_id: int):
    with connect() as db:
        with db.transaction():
            cursor = db.execute("DELETE FROM food_entries WHERE id = %s", (entry_id,))
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Entry not found")


@app.get("/api/report")
def report(
    start_date: date = Query(...),
    end_date: date = Query(...),
    min_calories: float = Query(0, ge=0),
    max_calories: float = Query(10000, ge=0),
):
    if start_date > end_date:
        raise HTTPException(status_code=422, detail="Start date must be on or before end date")
    if min_calories > max_calories:
        raise HTTPException(status_code=422, detail="Minimum calories must be at most maximum calories")
    with connect() as db:
        rows = db.execute(
            "SELECT e.*, f.name AS food_name FROM food_entries e JOIN foods f ON f.id = e.food_id "
            "WHERE e.entry_date BETWEEN %s AND %s AND e.calories BETWEEN %s AND %s "
            "ORDER BY e.entry_date, e.id",
            (start_date.isoformat(), end_date.isoformat(), min_calories, max_calories),
        ).fetchall()
    entries = [dict(row) for row in rows]
    totals = {
        key: round(sum(float(entry[key]) for entry in entries), 2)
        for key in ("calories", "protein_g", "carbs_g", "fat_g")
    }
    return {"entries": entries, "totals": totals, "count": len(entries)}
