from flask import Blueprint, request, current_app, jsonify
from flask_socketio import emit, join_room
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import socketio
from app.models.user import User

bp = Blueprint('notifications', __name__)

@socketio.on('connect')
@jwt_required()
def handle_connect():
    user_id = get_jwt_identity()
    # Create a private room for this user
    join_room(f"user_{user_id}")
    current_app.logger.info(f"User {user_id} connected to websocket")

# Function to send notification (call this from other routes)
def send_notification(user_id, notification_type, data):
    socketio.emit('notification', {
        'type': notification_type,
        'data': data
    }, room=f"user_{user_id}")

# # Example: Send friend request notification
# @bp.route('/friend-request', methods=['POST'])
# @jwt_required()
# def send_friend_request():
#     sender_id = get_jwt_identity()
#     recipient_id = request.json.get('recipient_id')
    
#     # Get sender info from database
#     sender = User.query.get(sender_id)
#     if not sender:
#         return jsonify({"error": "Sender not found"}), 404
    
#     # Send real-time notification
#     send_notification(recipient_id, 'friend_request', {
#         'sender_id': sender_id,
#         'sender_username': sender.username
#     })