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
    
# SocketIO event handlers for chat
@socketio.on('typing')
def handle_typing(data):
    current_app.logger.info(f"Typing event received: {data}")
    user_id = data.get('user_id')
    room_id = data.get('room_id')
    participants = data.get('participants')

    for participant in participants:
        current_app.logger.info(f"Emitting typing event to user {participant}")
        socketio.emit('user_typing', {'username': participant['username'], 'room_id': room_id},
                       room=f"user_{participant['id']}")

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

    if not room_id or not content:
        return jsonify({"error": "Room ID and content are required"}), 400

    try:
        # Create a new chat message
        chat_message = ChatMessage(room_id=room_id, sender_id=user_id, content=content)
        db.session.add(chat_message)

        # Update sender's last_read_at
        user_assoc = UserChatAssociation.query.filter_by(
            user_id=user_id,
            chat_room_id=room_id
        ).first()
        user_assoc.last_read_at = db.func.current_timestamp()

        # Update the last message and timestamp in the chat room
        ChatMessage.update_last_message(room_id, content)

        # Get the sender's username and chat room
        sender = User.query.get(user_id)
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
        for room_user_id in chat_room.user_ids:
            socketio.emit('chat_message', message_data, room=f"user_{room_user_id}")

        return jsonify({"message_id": chat_message.id}), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error sending message: {str(e)}")
        return jsonify({"error": "Failed to send message"}), 500

# Route to view chat messages
@bp.route('/messages/<int:room_id>', methods=['GET'])
@jwt_required()
def get_messages(room_id):
    user_id = get_jwt_identity()
    
    # Mark messages as read when fetching them
    user_assoc = UserChatAssociation.query.filter_by(
        user_id=user_id,
        chat_room_id=room_id
    ).first()
    user_assoc.last_read_at = db.func.current_timestamp()
    db.session.commit()
    
    messages = ChatMessage.query.filter_by(room_id=room_id).order_by(ChatMessage.timestamp.asc()).all()
    room = ChatRoom.query.get(room_id)

    room_messages = [{
        "id": message.id,
        "sender_id": message.sender_id,
        "sender_name": User.query.get(message.sender_id).username,
        "content": message.content,
        "timestamp": message.timestamp
    } for message in messages]

    room_name = room.name if room.is_group else User.query.join(UserChatAssociation).filter(
        UserChatAssociation.chat_room_id == room.id,
        UserChatAssociation.user_id != user_id
    ).first().username

    return jsonify({
        "room_name": room_name,
        "messages": room_messages
    }), 200

# Route to retrieve all chat rooms for the current user
@bp.route('/my-rooms', methods=['GET'])
@jwt_required()
def get_my_rooms():
    user_id = get_jwt_identity()
    
    # Get all chat rooms for the current user, ordered by last message timestamp
    chat_associations = (UserChatAssociation.query
        .join(ChatRoom)
        .filter(UserChatAssociation.user_id == user_id)
        .order_by(ChatRoom.last_message_timestamp.desc().nullslast())  # nullslast() puts rooms with no messages at the end
        .all())
    
    results = []

    for assoc in chat_associations:
        room = assoc.chat_room
        last_message_time = room.last_message_timestamp if room.last_message_timestamp else room.created_at
        time_passed = format_time_passed(last_message_time)

        # Count unread messages
        unread_count = ChatMessage.query.filter(
            ChatMessage.room_id == room.id,
            ChatMessage.timestamp > (assoc.last_read_at or room.created_at)
        ).count()
        
        results.append({
            "id": room.id,
            "name": room.name if room.is_group else User.query.join(UserChatAssociation).filter(
                UserChatAssociation.chat_room_id == room.id,
                UserChatAssociation.user_id != user_id
            ).first().username,
            "is_group": room.is_group,
            "lastMessage": room.last_message if room.last_message else "No messages yet",
            "timestamp": time_passed,
            "unread_count": unread_count
        })

    return jsonify({"rooms": results}), 200

@bp.route('/mark-all-read/<int:room_id>', methods=['POST'])
@jwt_required()
def mark_all_read(room_id):
    user_id = get_jwt_identity()
    
    # Find the user's association with the chat room
    user_assoc = UserChatAssociation.query.filter_by(
        user_id=user_id,
        chat_room_id=room_id
    ).first()

    if not user_assoc:
        return jsonify({"error": "User is not part of this chat room."}), 404

    # Update the last_read_at timestamp to the current time
    user_assoc.last_read_at = db.func.current_timestamp()
    
    socketio.emit('mark_all_read', room=f"user_{user_id}")
    
    try:
        db.session.commit()
        return jsonify({"message": "All messages marked as read."}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error marking messages as read: {str(e)}")
        return jsonify({"error": "Failed to mark messages as read."}), 500

@bp.route('/participants/<int:room_id>', methods=['GET'])
@jwt_required()
def get_chat_room_participants(room_id):
    user_id = get_jwt_identity()
    
    # Check if the user is part of the chat room
    user_association = UserChatAssociation.query.filter_by(
        chat_room_id=room_id,
        user_id=user_id
    ).first()
    
    if not user_association:
        return jsonify({"error": "User is not a participant of this chat room."}), 403
    
    # Query the UserChatAssociation to get participants of the chat room excluding the current user
    participants = UserChatAssociation.query.filter(
        UserChatAssociation.chat_room_id == room_id,
        UserChatAssociation.user_id != user_id
    ).all()
    
    # Extract user IDs and usernames
    participant_info = []
    for participant in participants:
        user = User.query.get(participant.user_id)
        if user:
            participant_info.append({
                "id": user.id,
                "username": user.username
            })
    
    return jsonify({
        "current_user_id": user_id,
        "participants": participant_info
    }), 200 