from app import db

class Profile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    bio = db.Column(db.Text)
    links = db.Column(db.JSON)  # Store links as JSON
    games = db.Column(db.JSON)  # Store games as JSON
    
    # Relationship with Media
    # media = db.relationship('Media', backref='profile', lazy='dynamic') 