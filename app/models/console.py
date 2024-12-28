from app import db
from datetime import datetime, UTC

class PlayStation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    psn_username = db.Column(db.String(80))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))

class Xbox(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    xbox_gamertag = db.Column(db.String(80))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))

class Steam(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    steam_username = db.Column(db.String(80))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))

class Nintendo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    friend_code = db.Column(db.String(80))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))

class Discord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    discord_username = db.Column(db.String(80))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
