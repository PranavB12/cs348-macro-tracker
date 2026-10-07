# Stage 2: Database Design and Demo

## Scope used for this demo

The repository did not include the text of Stage 1 Requirements 1 and 2. This implementation treats Requirement 1 as managing food log entries (insert, update, delete) and Requirement 2 as producing a filtered nutrition report. Confirm these labels against the submitted Stage 1 requirements before presenting.

## Database design

The demo runs on SQLite so it starts without a separate database server. The schema uses standard relational concepts and can be translated directly to MySQL (`INTEGER PRIMARY KEY AUTOINCREMENT` becomes `INT AUTO_INCREMENT PRIMARY KEY`; `REAL` becomes an appropriate `DECIMAL`). The live schema is initialized in `backend/main.py` by `initialize_database()`.

### `foods`

| Column | Type | Constraints | Purpose |
| --- | --- | --- | --- |
| `id` | integer | PK, auto increment | Food identifier |
| `name` | text | NOT NULL, UNIQUE | Food name used by the selector |
| `calories` | real | NOT NULL, >= 0 | kcal per serving |
| `protein_g` | real | NOT NULL, >= 0 | Protein per serving |
| `carbs_g` | real | NOT NULL, >= 0 | Carbohydrates per serving |
| `fat_g` | real | NOT NULL, >= 0 | Fat per serving |

### `food_entries`

| Column | Type | Constraints | Purpose |
| --- | --- | --- | --- |
| `id` | integer | PK, auto increment | Log entry identifier |
| `food_id` | integer | NOT NULL, FK -> `foods.id` | Selected catalog food |
| `entry_date` | text / date | NOT NULL | Day the food was consumed (ISO date) |
| `servings` | real / decimal | NOT NULL, > 0 | Number of catalog servings |
| `calories` | real / decimal | NOT NULL, >= 0 | Nutrition snapshot for this entry |
| `protein_g` | real / decimal | NOT NULL, >= 0 | Nutrition snapshot for this entry |
| `carbs_g` | real / decimal | NOT NULL, >= 0 | Nutrition snapshot for this entry |
| `fat_g` | real / decimal | NOT NULL, >= 0 | Nutrition snapshot for this entry |
| `created_at` | timestamp | NOT NULL, default current timestamp | Audit timestamp |

Relationship: one food can appear in many food entries (`foods.id` -> `food_entries.food_id`). A log entry stores calculated nutrition values when created or updated, preserving past reports if a catalog value changes later. An index on `food_entries.entry_date` supports date-range reports.

## Demo run of show (about 8 minutes)

Start the backend and frontend using the commands in the root README. Open the Vite URL, then use today's date so the initial date filter includes the records you add.

1. **0:00-1:00 | Design.** Show this schema, identify the primary keys and `food_entries.food_id` foreign key, and explain the one-to-many relationship and nutrition snapshot.
2. **1:00-2:00 | Dynamic selector.** In `backend/main.py`, show `GET /api/foods` querying `foods`. In `frontend/src/App.jsx`, show `refresh()` fetching `/foods` and the `foods.map(...)` that creates each `<option>`. Food names are stored in the database, not embedded as interface options.
3. **2:00-4:30 | Requirement 1 CRUD.** Add an Oats entry for today with 1 serving. Edit it to 1.5 servings and save; show calories/macros update. Add a second food entry, then delete that entry. Point to `POST /api/entries`, `PUT /api/entries/{entry_id}`, and `DELETE /api/entries/{entry_id}` and their matching UI handlers `saveEntry()` and `removeEntry()`.
4. **4:30-7:00 | Requirement 2 report.** Set From and To to today's date and choose a calorie range that includes the 1.5 serving Oats row (225-225 kcal). Apply filters and show the report and totals. Before changing the row, note the displayed result. Edit servings to 2 and save; the report refreshes to reflect 300 kcal, which no longer matches the previous range. Widen the max to 300 and apply to show the changed report. Explain that `/api/report` filters by date and per-entry calorie range and computes totals from the selected rows.
5. **7:00-8:00 | Source walkthrough.** Show the SQL in `report()` and the API-backed table rendering in `App.jsx`. Mention validation for positive serving counts, ordered date bounds, and minimum/maximum calorie bounds.

For the report change sequence, leave the calorie filter at 225-225 kcal after the first result, edit Oats from 1.5 servings to 2, apply (zero rows), then widen to 0-300 kcal and apply (the 300 kcal row returns). This makes the before/after effect easy to see.

## Source map

- Database initialization, constraints, seed data, and CRUD/report SQL: `backend/main.py`
- Dynamic food selector, CRUD form, report filters, totals, and results table: `frontend/src/App.jsx`
- Local responsive presentation: `frontend/src/App.css`
