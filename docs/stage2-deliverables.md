# Stage 2: Database Design and Demo

## Scope used for this demo

Stage 1 established the React/Vite and FastAPI stack and a working web page. Stage 2 separately asks for CRUD on one table, a filtered report before and after a data change, and a database populated UI component. The current Macro Tracker is the evolved working page on that stack. The rubric's “Requirement 1” and “Requirement 2” labels for the CRUD and report demonstrations are treated here as those Stage 2 workflows.

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

1. **0:00-0:30 | Stack and app.** Briefly name React/Vite and FastAPI, then show the current app running in the browser. The README has the install and run commands if asked.
2. **0:30-1:30 | Database design.** Show this schema, identify the primary keys and `food_entries.food_id` foreign key, and explain the one-to-many relationship and nutrition snapshot.
3. **1:30-2:30 | Database-driven selector.** In `backend/main.py`, show `GET /api/foods` querying `foods`. In `frontend/src/App.jsx`, show `refresh()` fetching `/foods` and the `foods.map(...)` that creates each `<option>`. Food names are stored in the database, not embedded as interface options.
4. **2:30-5:00 | CRUD workflow.** Add an Oats entry for today with 1 serving. Edit it to 1.5 servings and save; show calories/macros update. Add a second food entry, then delete that entry. Point to `POST /api/entries`, `PUT /api/entries/{entry_id}`, and `DELETE /api/entries/{entry_id}` and their matching UI handlers `saveEntry()` and `removeEntry()`.
5. **5:00-8:00 | Filtered report.** Set From and To to today's date and the calorie range to 225-225 kcal. Apply filters and show the 1.5 serving Oats result and totals. Edit servings to 2 and save; it drops out of the old range. Widen the range to 0-300 kcal and apply to show the updated 300 kcal row and totals. Explain that `/api/report` filters by date and per-entry calorie range and computes totals from selected rows.

For the report change sequence, leave the calorie filter at 225-225 kcal after the first result, edit Oats from 1.5 servings to 2, then widen to 0-300 kcal and apply (the 300 kcal row returns). This makes the before/after effect easy to see.

## Source map

- Database initialization, constraints, seed data, and CRUD/report SQL: `backend/main.py`
- Dynamic food selector, CRUD form, report filters, totals, and results table: `frontend/src/App.jsx`
- Local responsive presentation: `frontend/src/App.css`
