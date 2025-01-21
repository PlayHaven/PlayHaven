from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db, socketio
from app.models.user import User
from app.models.chat import ChatRoom, ChatMessage, UserChatAssociation
from app.utils.error_handler import handle_route_errors

bp = Blueprint('chat', __name__, url_prefix='/api/chat')

# New helper function to format time passed
def format_time_passed(timestamp):
    from datetime import datetime, timedelta

    now = datetime.utcnow()
    time_diff = now - timestamp

    if time_diff < timedelta(minutes=1):
        return "just now"
    elif time_diff < timedelta(hours=1):
        minutes = int(time_diff.total_seconds() // 60)
        return f"{minutes} min ago"
    elif time_diff < timedelta(days=1):
        hours = int(time_diff.total_seconds() // 3600)
        return f"{hours} hours ago"
    else:
        days = int(time_diff.total_seconds() // 86400)
        return f"{days} days ago" 

# Route to create a chat room
@bp.route('/create-room', methods=['POST'])
@jwt_required()
@handle_route_errors
def create_chat_room():
    user_id = get_jwt_identity()
    data = request.json

    # Check if it's a group chat or 1-to-1
    is_group = data.get('is_group', False)
    user_ids = data.get('user_ids', [])

    if is_group:
        if user_id not in user_ids:
            user_ids.append(int(user_id))
    else:
        if len(user_ids) != 1:
            return jsonify({"error": "For 1-to-1 chat, provide exactly one user ID."}), 400
        user_ids.append(int(user_id))

    current_app.logger.info(f"User IDs: {user_ids}")

    chat_room = ChatRoom(name=data.get('name'), is_group=is_group, user_ids=user_ids)
    db.session.add(chat_room)
    db.session.commit()
    
    current_app.logger.info(f"Chat room created: {chat_room.id}")
    
    for user_id in user_ids:
        user_chat_association = UserChatAssociation(user_id=user_id, chat_room_id=chat_room.id)
        db.session.add(user_chat_association)

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
    
    # Update the last message and timestamp in the chat room
    ChatMessage.update_last_message(room_id, content)

    # Get the sender's username
    sender = User.query.get(user_id)
    
    # Get all users in this chat room
    chat_room = ChatRoom.query.get(room_id)
    
    db.session.commit()

    # Emit the message to all users in the chat room
    message_data = {
        "id": int(chat_message.id),
        "room_id": int(room_id),
        "sender_id": int(user_id),
        "sender_name": sender.username,
        "content": content,
        "timestamp": chat_message.timestamp.isoformat()
    }

    # Emit to all users in the chat room
    for user_id in chat_room.user_ids:
        socketio.emit('chat_message', message_data, room=f"user_{user_id}")

    return jsonify({"message_id": chat_message.id}), 201

# Route to view chat messages
@bp.route('/messages/<int:room_id>', methods=['GET'])
@jwt_required()
def get_messages(room_id):
    user_id = get_jwt_identity()
    messages = ChatMessage.query.filter_by(room_id=room_id).order_by(ChatMessage.timestamp.asc()).all()
    room = ChatRoom.query.get(room_id)

    room_messages = [{
        "id": message.id,
        "sender_id": message.sender_id,
        "sender_name": User.query.get(message.sender_id).username,
        "content": message.content,
        "timestamp": message.timestamp
    } for message in messages]

    room_name = room.name if room.is_group else User.query.join(UserChatAssociation).filter(UserChatAssociation.chat_room_id == room.id, UserChatAssociation.user_id != user_id).first().username

    return jsonify({
        "room_name": room_name,
        "messages": room_messages
    }), 200 

# Route to retrieve all chat rooms for the current user
@bp.route('/my-rooms', methods=['GET'])
@jwt_required()
def get_my_rooms():
    user_id = get_jwt_identity()
    
    # Query for chat rooms that include the current user
    chat_rooms = UserChatAssociation.query.filter_by(user_id=user_id).all()
    current_app.logger.info(f"Chat rooms: {chat_rooms}")
    results = []

    for chat_room in chat_rooms:
        room = ChatRoom.query.get(chat_room.chat_room_id)
        last_message_time = room.last_message_timestamp
        time_passed = format_time_passed(last_message_time)  # New function to format time passed
        
        results.append({
            "id": room.id,
            "name": room.name if room.is_group else User.query.join(UserChatAssociation).filter(UserChatAssociation.chat_room_id == room.id, UserChatAssociation.user_id != user_id).first().username,
            "is_group": room.is_group,
            "lastMessage": room.last_message,
            "timestamp": time_passed  # Updated to use formatted time passed
        })

    return jsonify({"rooms": results}), 200 