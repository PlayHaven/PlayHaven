from app import db

class ChatRoom(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=True)  # For group chats
    is_group = db.Column(db.Boolean, default=False)  # True for group chats
    user_ids = db.Column(db.JSON, nullable=False)  # List of user IDs in the chat room
    last_message = db.Column(db.Text, nullable=True)  # Content of the last message
    last_message_timestamp = db.Column(db.DateTime, nullable=True)  # Timestamp of the last message

class UserChatAssociation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    chat_room_id = db.Column(db.Integer, db.ForeignKey('chat_room.id'), nullable=False)

class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('chat_room.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

    room = db.relationship('ChatRoom', backref='messages')
    sender = db.relationship('User', backref='sent_messages')

    @staticmethod
    def update_last_message(room_id, content):
        room = ChatRoom.query.get(room_id)
        if room:
            room.last_message = content
            room.last_message_timestamp = db.func.current_timestamp()
            db.session.commit()
