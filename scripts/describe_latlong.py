import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from app import app
from extensions import db

with app.app_context():
    try:
        from sqlalchemy import text
        res = db.session.execute(text('DESCRIBE latlongdata'))
        print('latlongdata columns:')
        for row in res.fetchall():
            print(tuple(row))
    except Exception as e:
        print('Error describing table:', e)
