import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from app import app
from models import Post

with app.app_context():
    try:
        pc = Post.query.count()
        print('posts count:', pc)
        first = Post.query.order_by(Post.id).first()
        if first:
            print('first post:', first.id, first.name, first.lat, first.lng)
        else:
            print('no posts found')
    except Exception as e:
        print('Error querying posts:', e)
