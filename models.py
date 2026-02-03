from extensions import db
from datetime import datetime

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(128), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(32), default='viewer')

    def __repr__(self):
        return f"<User {self.username}>"

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    lat = db.Column(db.Float, nullable=False)
    lng = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(64))
    area = db.Column(db.String(128))
    connections = db.relationship('ConnectionPoint', back_populates='post')

    def __repr__(self):
        return f"<Post {self.name} ({self.lat}, {self.lng})>"

class Connection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    total_length = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    points = db.relationship('ConnectionPoint', back_populates='connection', cascade='all, delete-orphan', order_by='ConnectionPoint.seq')

    def __repr__(self):
        return f"<Connection {self.id} ({self.total_length} m)>"

class ConnectionPoint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    connection_id = db.Column(db.Integer, db.ForeignKey('connection.id'), nullable=False)
    seq = db.Column(db.Integer, nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=True)
    lat = db.Column(db.Float, nullable=False)
    lng = db.Column(db.Float, nullable=False)
    segment_length = db.Column(db.Float)

    connection = db.relationship('Connection', back_populates='points')
    post = db.relationship('Post', back_populates='connections')

    def __repr__(self):
        return f"<CP conn={self.connection_id} seq={self.seq} post={self.post_id}>"


class LatLongData(db.Model):
    """Represents existing table `latlongdata` with columns: post_id, latitude, longitude
    This maps to your external MySQL table and can be used to import/merge coordinates.
    """
    __tablename__ = 'latlongdata'

    post_id = db.Column(db.Integer, primary_key=True)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f"<LatLong post_id={self.post_id} ({self.latitude},{self.longitude})>"