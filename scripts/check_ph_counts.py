import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from app import app
from models import Post

with app.app_context():
    print('total posts:', Post.query.count())
    ph_count = Post.query.filter(Post.lat >= 4.0, Post.lat <= 22.0, Post.lng >= 116.0, Post.lng <= 127.5).count()
    print('posts in PH bbox:', ph_count)
    example = Post.query.filter(Post.lat >= 4.0, Post.lat <= 22.0, Post.lng >= 116.0, Post.lng <= 127.5).limit(3).all()
    print('sample:', [(p.id, p.lat, p.lng) for p in example])
