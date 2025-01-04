from app import db
from datetime import datetime, UTC

class Media(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    media_type = db.Column(db.String(10))
    file_path = db.Column(db.String(255))
    storage_type = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    
    user = db.relationship("User", back_populates="media")
    # Add relationship to comments
    comments = db.relationship('Comment', backref='media', lazy='dynamic', cascade='all, delete-orphan')

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    media_id = db.Column(db.Integer, db.ForeignKey('media.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    
    # Relationship with User
    user = db.relationship('User', backref='comments') 