from app import db

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    notification_type = db.Column(db.String(50), nullable=False)
    viewed = db.Column(db.Boolean, default=False)
    data = db.Column(db.JSON, nullable=False)  # Store additional data as JSON
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    user = db.relationship('User', backref='notifications')

    # Define notification types as class constants
    FRIEND_REQUEST = 'friend_request'
    FRIEND_REQUEST_ACCEPTED = 'friend_request_accepted'
    FRIEND_REQUEST_REJECTED = 'friend_request_rejected'
    MESSAGE = 'message'
    COMMENT = 'comment'
    LIKE = 'like'
    # Add more types as needed

    def __repr__(self):
        return f'<Notification {self.id} for User {self.user_id}>' 