import os
import sys
# Ensure project root is on sys.path so we can import app and models
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import app
from models import LatLongData, Post

with app.app_context():
    try:
        ll_count = LatLongData.query.count()
        print('latlongdata count:', ll_count)
        first = LatLongData.query.first()
        if first:
            print('first row:', first.post_id, first.latitude, first.longitude)
        else:
            print('first row: None')

        post_count = Post.query.count()
        print('posts count:', post_count)
        post_first = Post.query.first()
        if post_first:
            print('first post:', post_first.id, post_first.name, post_first.lat, post_first.lng)
        else:
            print('first post: None')
    except Exception as e:
        print('Error querying database:', e)
