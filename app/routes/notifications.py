from flask import Blueprint, request, current_app, jsonify
from flask_socketio import emit, join_room
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import socketio, db
from app.models.user import User
from app.models.notification import Notification
from app.utils.error_handler import handle_route_errors

bp = Blueprint('notifications', __name__, url_prefix='/api/notifications')

@socketio.on('connect')
@jwt_required()
def handle_connect():
    user_id = get_jwt_identity()
    # Create a private room for this user
    join_room(f"user_{user_id}")
    current_app.logger.info(f"User {user_id} connected to websocket")

# Function to send notification and save it to the database
def send_notification(user_id, notification_type, data):
    # Create a new notification instance
    notification = Notification(
        user_id=user_id,
        notification_type=notification_type,
        data=data
    )
    
    # Save the notification to the database
    db.session.add(notification)
    db.session.commit()
    
    # Emit the notification to the user's WebSocket room
    socketio.emit('notification', {
        'type': notification_type,
        'data': data
    }, room=f"user_{user_id}")

@bp.route('/', methods=['GET'])
@jwt_required()
def get_notifications():
    user_id = get_jwt_identity()
    notifications = Notification.query.filter_by(user_id=user_id).order_by(Notification.created_at.desc()).all()
    
    results = [{
        "id": notification.id,
        "type": notification.notification_type,
        "data": notification.data,
        "viewed": notification.viewed,
        "created_at": notification.created_at
    } for notification in notifications]
    
    return jsonify({"notifications": results}), 200

@bp.route('/read-all', methods=['PUT'])
@jwt_required()
@handle_route_errors
def read_all_notifications():
    user_id = get_jwt_identity()

    notifications = Notification.query.filter_by(user_id=user_id).order_by(Notification.created_at.desc()).all()
    for notif in notifications:
        notif.viewed = True
        db.session.add(notif)

    db.session.commit()

    results = [{
        "id": notif.id,
        "type": notif.notification_type,
        "data": notif.data,
        "viewed": notif.viewed,
        "created_at": notif.created_at
    } for notif in notifications]
    
    return jsonify({"notifications": results}), 200