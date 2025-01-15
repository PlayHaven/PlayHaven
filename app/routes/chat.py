from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.chat import ChatRoom, ChatMessage

bp = Blueprint('chat', __name__, url_prefix='/api/chat')

# Route to create a chat room
@bp.route('/create-room', methods=['POST'])
@jwt_required()
def create_chat_room():
    user_id = get_jwt_identity()
    data = request.json

    # Check if it's a group chat or 1-to-1
    is_group = data.get('is_group', False)
    user_ids = data.get('user_ids', [])

    if is_group:
        # Ensure the current user is included in the group
        if user_id not in user_ids:
            user_ids.append(user_id)
    else:
        # For 1-to-1 chat, ensure only two users
        if len(user_ids) != 1:
            return jsonify({"error": "For 1-to-1 chat, provide exactly one user ID."}), 400
        user_ids.append(user_id)

    # Create the chat room
    chat_room = ChatRoom(name=data.get('name'), is_group=is_group, user_ids=user_ids)
    db.session.add(chat_room)
    db.session.commit()

    return jsonify({"room_id": chat_room.id}), 201

# Route to send a chat message
@bp.route('/send-message', methods=['POST'])
@jwt_required()
def send_message():
    user_id = get_jwt_identity()
    data = request.json

    room_id = data.get('room_id')
    content = data.get('content')

    # Create a new chat message
    chat_message = ChatMessage(room_id=room_id, sender_id=user_id, content=content)
    db.session.add(chat_message)
    db.session.commit()

    return jsonify({"message_id": chat_message.id}), 201

# Route to view chat messages
@bp.route('/messages/<int:room_id>', methods=['GET'])
@jwt_required()
def get_messages(room_id):
    messages = ChatMessage.query.filter_by(room_id=room_id).order_by(ChatMessage.timestamp.asc()).all()

    results = [{
        "id": message.id,
        "sender_id": message.sender_id,
        "content": message.content,
        "timestamp": message.timestamp
    } for message in messages]

    return jsonify({"messages": results}), 200 