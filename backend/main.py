import os
import sqlite3
from contextlib import closing
from datetime import date
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


DATABASE_PATH = Path(os.getenv("DATABASE_PATH", Path(__file__).with_name("macro_tracker.db")))
SEED_FOODS = [
    ("Oats", 150, 5.0, 27.0, 3.0),
    ("Greek yogurt", 100, 17.0, 6.0, 0.0),
    ("Banana", 105, 1.3, 27.0, 0.4),
    ("Chicken breast", 165, 31.0, 0.0, 3.6),
    ("Brown rice", 216, 5.0, 45.0, 1.8),
    ("Avocado", 160, 2.0, 9.0, 14.7),
]


def connect():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with closing(connect()) as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS foods (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                calories REAL NOT NULL CHECK (calories >= 0),
                protein_g REAL NOT NULL CHECK (protein_g >= 0),
                carbs_g REAL NOT NULL CHECK (carbs_g >= 0),
                fat_g REAL NOT NULL CHECK (fat_g >= 0)
            );
            CREATE TABLE IF NOT EXISTS food_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                food_id INTEGER NOT NULL REFERENCES foods(id),
                entry_date TEXT NOT NULL,
                servings REAL NOT NULL CHECK (servings > 0),
                calories REAL NOT NULL CHECK (calories >= 0),
                protein_g REAL NOT NULL CHECK (protein_g >= 0),
                carbs_g REAL NOT NULL CHECK (carbs_g >= 0),
                fat_g REAL NOT NULL CHECK (fat_g >= 0),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_food_entries_date ON food_entries(entry_date);
            """
        )
        count = db.execute("SELECT COUNT(*) FROM foods").fetchone()[0]
        if count == 0:
            db.executemany(
                "INSERT INTO foods (name, calories, protein_g, carbs_g, fat_g) VALUES (?, ?, ?, ?, ?)",
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
    with closing(connect()) as db:
        return [dict(row) for row in db.execute("SELECT * FROM foods ORDER BY name")]


def entry_values(db, payload: EntryInput):
    food = db.execute("SELECT * FROM foods WHERE id = ?", (payload.food_id,)).fetchone()
    if food is None:
        raise HTTPException(status_code=404, detail="Food not found")
    servings = payload.servings
    return (
        payload.food_id,
        payload.entry_date.isoformat(),
        servings,
        *(round(food[key] * servings, 2) for key in ("calories", "protein_g", "carbs_g", "fat_g")),
    )


@app.post("/api/entries", status_code=201)
def create_entry(payload: EntryInput):
    with closing(connect()) as db:
        values = entry_values(db, payload)
        cursor = db.execute(
            "INSERT INTO food_entries (food_id, entry_date, servings, calories, protein_g, carbs_g, fat_g) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)", values
        )
        db.commit()
        return dict(db.execute("SELECT * FROM food_entries WHERE id = ?", (cursor.lastrowid,)).fetchone())


@app.put("/api/entries/{entry_id}")
def update_entry(entry_id: int, payload: EntryInput):
    with closing(connect()) as db:
        if db.execute("SELECT id FROM food_entries WHERE id = ?", (entry_id,)).fetchone() is None:
            raise HTTPException(status_code=404, detail="Entry not found")
        values = entry_values(db, payload)
        db.execute(
            "UPDATE food_entries SET food_id = ?, entry_date = ?, servings = ?, calories = ?, "
            "protein_g = ?, carbs_g = ?, fat_g = ? WHERE id = ?",
            (*values, entry_id),
        )
        db.commit()
        return dict(db.execute("SELECT * FROM food_entries WHERE id = ?", (entry_id,)).fetchone())


@app.delete("/api/entries/{entry_id}", status_code=204)
def delete_entry(entry_id: int):
    with closing(connect()) as db:
        cursor = db.execute("DELETE FROM food_entries WHERE id = ?", (entry_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Entry not found")
        db.commit()


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
    with closing(connect()) as db:
        rows = db.execute(
            "SELECT e.*, f.name AS food_name FROM food_entries e JOIN foods f ON f.id = e.food_id "
            "WHERE e.entry_date BETWEEN ? AND ? AND e.calories BETWEEN ? AND ? "
            "ORDER BY e.entry_date, e.id",
            (start_date.isoformat(), end_date.isoformat(), min_calories, max_calories),
        ).fetchall()
    entries = [dict(row) for row in rows]
    totals = {
        key: round(sum(entry[key] for entry in entries), 2)
        for key in ("calories", "protein_g", "carbs_g", "fat_g")
    }
    return {"entries": entries, "totals": totals, "count": len(entries)}
