# Stage 3 deliverables

## Project links

- Application (local demo): http://localhost:5173 (start the backend at http://localhost:8000 first; see the setup steps in the [README](../README.md)). No public deployment is configured.
- Source code: https://github.com/PranavB12/cs348-macro-tracker
- Demo recording: record a 5–10 minute walkthrough using the timed outline below, then submit the recording alongside these deliverables.

## Demo outline (about 7 minutes)

| Time | Show and explain |
| --- | --- |
| 0:00–0:45 | Open the tracker, show the food catalog, add/edit/delete controls, and nutrition report. Set the date filter to include the entry you will add. |
| 0:45–2:15 | Show `backend/main.py`: `EntryInput` validates `food_id`, `entry_date`, and `servings`; `entry_values` verifies the food exists. Explain that validation helps reject malformed values, while the main SQL injection defense is parameter binding. |
| 2:15–3:00 | Show `Database.execute`/`executemany` and examples in `entry_values`, `create_entry`, `update_entry`, `delete_entry`, and `report`. Values are passed separately as `%s` parameters, so user data remains data rather than SQL syntax. Demonstrate entering a quote/payload as a food id or report value: validation rejects an invalid typed value, and valid text filters are bound as values. Point out that table/column identifiers are fixed in application code, never accepted from the browser. |
| 3:00–4:45 | Show `initialize_database` and discuss every index below. Trace the report route to the frontend's “Apply filters” report. The date range and calorie bounds are bound in the `WHERE` clause; sorting is by date and id. Explain the leftmost-prefix behavior for the composite index and that actual selection can be confirmed with `EXPLAIN` on a populated database. |
| 4:45–6:30 | Show `DATABASE_CONFIG` and `Database.transaction`, then the three write routes. Add an entry and edit or delete it. Explain that a multi-step create (food lookup + insert + readback) or update is one transaction; any error rolls it back. InnoDB provides atomicity and row locking. |
| 6:30–7:30 | Explain `READ COMMITTED`: every query sees rows committed before that query, so another user's completed write becomes visible on the next report query, without dirty reads. Concurrent writes to the same row are protected by InnoDB row locks; conflicting changes serialize, and later updates can overwrite earlier edits (last successful update wins). This is suitable for this tracker; it does not promise repeatable reads across separate report statements. Finish with the source link and local app URL. |

## SQL injection protection

The backend uses PyMySQL parameterized statements throughout. For example, the report query contains fixed SQL with placeholders and supplies `(start_date, end_date, min_calories, max_calories)` separately. Entry lookups and mutations likewise bind ids and nutrition values separately. Pydantic types and bounds validate API inputs, but escaping or sanitizing strings is not used as a substitute for parameterization. The frontend also serializes report filters with `URLSearchParams`; SQL safety is enforced at the backend boundary.

## Indexes and the queries/reports they support

All tables use InnoDB. `foods.id` and `food_entries.id` are primary-key indexes. `foods.name` has a unique index from `UNIQUE`; it enforces unique catalog names. The foreign key `food_entries.food_id → foods.id` is indexed by InnoDB (the schema does not name that automatically created index). The application uses these key indexes for food lookup/join and entry id lookup/update/delete.

| Index | Benefiting query and app location | Why it helps |
| --- | --- | --- |
| `idx_food_entries_date (entry_date)` | `GET /api/report`, the nutrition report in `backend/main.py`; range predicate `entry_date BETWEEN ...` and ordering by date | Narrows entries to the requested date range and supports date ordering. |
| `idx_food_entries_date_calories (entry_date, calories)` | Same report: date range plus `calories BETWEEN ...` | The leading date column serves the date range; calorie values can further help within matching date keys. MySQL may use the second column less fully when the first column is a range. `EXPLAIN` on the actual data can show the chosen access path. |
| `foods.PRIMARY`, `foods.name` unique, `food_entries.PRIMARY`, and the foreign-key index on `food_id` | `GET /api/foods` ordering/selection, `entry_values` food lookup, report join, and entry id operations | Support key lookups, enforce uniqueness/referential integrity, and support the join. |

The composite index is installed on existing Stage 2 databases at startup: `CREATE TABLE IF NOT EXISTS` alone does not alter an existing table. The report currently selects `e.*`, so it is not a covering index. Additional indexes increase write/storage cost; these indexes target the app's primary read and integrity paths.

To inspect the plan on a local database, run:

```sql
EXPLAIN
SELECT e.*, f.name AS food_name
FROM food_entries e JOIN foods f ON f.id = e.food_id
WHERE e.entry_date BETWEEN '2026-01-01' AND '2026-12-31'
  AND e.calories BETWEEN 0 AND 10000
ORDER BY e.entry_date, e.id;
```

## Transactions and concurrency

PyMySQL connections run with `autocommit=False`, and each connection explicitly sets MySQL's session isolation to `READ COMMITTED`. `Database.transaction()` begins a transaction, commits only after the whole route operation succeeds, and rolls back on exceptions. Create, update, and delete use this wrapper. In particular, update's existence check, nutrition lookup, write, and readback form a single atomic unit; a missing food or entry cannot leave a partial update behind. InnoDB supplies row-level locks and foreign-key enforcement.

The Stage 2 app had no account model, but its shared database can receive requests from multiple users. Under `READ COMMITTED`, two report statements can see different committed states if another user writes between them. Two users updating the same entry are serialized by row locking; the later committed update replaces the earlier values. For this simple tracker, that tradeoff avoids dirty reads while keeping each operation atomic. A future version needing repeatable multi-query reports or conflict detection could use `REPEATABLE READ` snapshots or an optimistic version column.
