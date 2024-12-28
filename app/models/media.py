from app import db
from datetime import datetime, UTC

class Media(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('profile.id'), nullable=False)
    media_type = db.Column(db.String(10))  # 'photo' or 'video'
    file_path = db.Column(db.String(255))
    uploaded_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC)) 