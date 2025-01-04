from datetime import datetime, UTC
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    first_name = db.Column(db.String(80))
    last_name = db.Column(db.String(80))
    password_hash = db.Column(db.String(256), nullable=False)
    birth_date = db.Column(db.Integer)
    birth_month = db.Column(db.Integer)
    birth_year = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    
    # Relationship with Profile
    profile = db.relationship('Profile', backref='user', uselist=False)
    
    # Add this line to establish the two-way relationship
    media = db.relationship('Media', back_populates='user')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)