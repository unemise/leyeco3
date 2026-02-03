from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
import os

from extensions import db, migrate

load_dotenv()

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# Configure database (MySQL recommended for production)
# Support either a single DATABASE_URL or individual DB_* environment variables
database_url = os.getenv('DATABASE_URL')
if not database_url:
    db_user = os.getenv('DB_USERNAME')
    db_pass = os.getenv('DB_PASSWORD')
    db_host = os.getenv('DB_HOST', '127.0.0.1')
    db_port = os.getenv('DB_PORT', '3306')
    db_name = os.getenv('DB_DATABASE')
    if db_user and db_name is not None:
        # Build a sqlalchemy URL for PyMySQL driver
        if db_pass:
            database_url = f"mysql+pymysql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
        else:
            database_url = f"mysql+pymysql://{db_user}@{db_host}:{db_port}/{db_name}"
    else:
        database_url = 'sqlite:///app.db'

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Bind extensions to app
db.init_app(app)
migrate.init_app(app, db)

# Import models after DB is available to avoid circular imports
with app.app_context():
    import models  # noqa: E402,F401
    # Bring commonly used model names into this module namespace
    from models import Post  # noqa: E402,F401
# Sample in-memory posts — used as a fallback if DB is empty
POSTS = [
    {"id": 1, "name": "Pole A", "lat": 40.7128, "lng": -74.0060, "status": "active"},
    {"id": 2, "name": "Pole B", "lat": 40.7138, "lng": -74.0050, "status": "maintenance"},
]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/posts')
def api_posts():
    """Return posts. Optional query arg `in_ph=1` filters to posts within Philippines bounding box."""
    in_ph = str(request.args.get('in_ph', '')).lower() in ('1', 'true', 'yes')
    try:
        query = Post.query
        if in_ph:
            # Filter in DB for performance
            query = query.filter(Post.lat >= 4.0, Post.lat <= 22.0, Post.lng >= 116.0, Post.lng <= 127.5)
        db_posts = query.all()
        posts = [{"id": p.id, "name": p.name, "lat": p.lat, "lng": p.lng, "status": p.status} for p in db_posts]
        if posts:
            return jsonify(posts)
    except Exception:
        pass
    # Fallback to in-memory POSTS (optionally filtered)
    if in_ph:
        filtered = [p for p in POSTS if p['lat'] >= 4.0 and p['lat'] <= 22.0 and p['lng'] >= 116.0 and p['lng'] <= 127.5]
        return jsonify(filtered)
    return jsonify(POSTS)


@app.route('/api/import_latlong', methods=['POST'])
def api_import_latlong():
    """Import coordinates from `latlongdata` table into `posts` table (upsert by post_id).
    Call via: POST /api/import_latlong
    Returns JSON with import stats.
    """
    try:
        from import_latlong import import_from_latlong
        stats = import_from_latlong()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# New endpoint to return raw latlongdata normalized to post_id/lat/lng
from sqlalchemy import text

@app.route('/api/latlongdata')
def api_latlongdata():
    """Return normalized rows from `latlongdata` table as JSON: [{post_id, lat, lng}, ...]
    Column names are detected; if not present, the first three columns are used in order.
    """
    try:
        desc = db.session.execute(text('DESCRIBE latlongdata')).fetchall()
        col_names = [row[0] for row in desc]
        lower_cols = [c.lower() for c in col_names]
        expected = ['post_id', 'latitude', 'longitude']
        mapping = {}
        for name in expected:
            if name in lower_cols:
                mapping[name] = col_names[lower_cols.index(name)]

        if not all(k in mapping for k in expected):
            if len(col_names) < 3:
                return jsonify({'error': 'latlongdata must have at least 3 columns'}), 400
            mapping = {'post_id': col_names[0], 'latitude': col_names[1], 'longitude': col_names[2]}

        sql = text(f"SELECT `{mapping['post_id']}` AS post_id, `{mapping['latitude']}` AS latitude, `{mapping['longitude']}` AS longitude FROM latlongdata")
        rows = db.session.execute(sql).fetchall()

        out = []
        for r in rows:
            # Support different Row types: mapping by name (SQLAlchemy Row._mapping) or tuple-like
            if hasattr(r, '_mapping'):
                mapping = r._mapping
            else:
                # Fallback: map by positional columns (0=post_id,1=latitude,2=longitude)
                mapping = {
                    'post_id': r[0] if len(r) > 0 else None,
                    'latitude': r[1] if len(r) > 1 else None,
                    'longitude': r[2] if len(r) > 2 else None,
                }

            try:
                pid_raw = mapping.get('post_id')
                pid = int(pid_raw) if pid_raw is not None else None
            except Exception:
                pid = None
            try:
                lat_raw = mapping.get('latitude')
                lng_raw = mapping.get('longitude')
                lat = float(lat_raw) if lat_raw is not None else None
                lng = float(lng_raw) if lng_raw is not None else None
            except Exception:
                lat = None
                lng = None
            out.append({'post_id': pid, 'lat': lat, 'lng': lng})

        return jsonify(out)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    debug = os.getenv('FLASK_ENV') == 'development'
    app.run(debug=debug, host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
