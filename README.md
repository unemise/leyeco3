# Interactive Electrical Post Mapping & Connection System

Quick start (Windows):

1. Create a virtual environment:

```powershell
python -m venv venv
venv\Scripts\Activate.ps1   # or venv\Scripts\activate for cmd
```

2. Install deps:

```powershell
pip install -r requirements.txt
```

3. Run the app:

```powershell
set FLASK_APP=app.py
set FLASK_ENV=development
python app.py
```

Open http://127.0.0.1:5000

Map behavior:
- Each post that has `latitude` and `longitude` will appear as a pin on the map.
- When the app loads, the map will automatically center on the first available post and open its popup so you are "auto-located" to the first post.
- Posts without valid coordinates are ignored by the map until coordinates are provided (use `import_latlong.py` or API to update).

Next steps: Use MySQL with SQLAlchemy and Flask-Migrate. Example steps:

1. Install MySQL server and create a database (e.g., `leyeco_db`).
2. Set your `DATABASE_URL` in `.env`:
   - `DATABASE_URL=mysql+pymysql://<user>:<password>@<host>/<dbname>`
3. Install deps:

```powershell
pip install -r requirements.txt
```

4. Initialize and run migrations:

```powershell
set FLASK_APP=app.py
flask db init     # only first time
flask db migrate -m "initial"
flask db upgrade
```

5. Seed sample data:

```powershell
python seed_db.py
```


Importing coordinates from existing `latlongdata` table

If you already have a MySQL table named `latlongdata` with columns `post_id`, `latitude`, and `longitude`, you can import/merge those coordinates into the app's `posts` table.

- To import from the command line:

```powershell
python import_latlong.py
```

- Or call the API endpoint (POST):

```powershell
curl -X POST http://127.0.0.1:5000/api/import_latlong
```

This will upsert rows by `post_id` (create missing posts as `Post <id>` and update existing posts' lat/lng). Import will now skip rows with invalid coordinates and rows outside the Philippines (approx lat 4.0..22.0, lng 116.0..127.5) and will report `skipped_outside_ph` in the import stats.

6. Run app:

```powershell
python app.py
```

Notes: For advanced GIS queries consider PostGIS (PostgreSQL) for spatial functions. Use `Flask-Migrate` for schema migrations and keep your `DATABASE_URL` secure (do not commit credentials).