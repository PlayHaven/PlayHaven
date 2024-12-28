from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.friendship import Friendship
from app import db
from app.models.user import User

bp = Blueprint('friendship', __name__, url_prefix='/api/friends')

@bp.route('/request', methods=['POST'])
@jwt_required()
def send_friend_request():
    user_id = get_jwt_identity()
    friend_username = request.json.get('username')
    
    current_app.logger.debug(f'Sending friend request from user_id: {user_id} to username: {friend_username}')
    
    # Find friend by username
    friend = User.query.filter_by(username=friend_username).first()
    if not friend:
        return jsonify({"error": "User not found"}), 404
        
    if str(user_id) == str(friend.id):
        return jsonify({"error": "Cannot friend yourself"}), 400
        
    existing = Friendship.query.filter_by(
        user_id=user_id,
        friend_id=friend.id
    ).first()
    
    if existing:
        return jsonify({"error": "Friend request already exists"}), 400
        
    friendship = Friendship(user_id=user_id, friend_id=friend.id)
    db.session.add(friendship)
    db.session.commit()
    
    current_app.logger.debug(f'Friend request sent successfully to {friend_username}')
    return jsonify({"message": "Friend request sent"}), 201

@bp.route('/accept', methods=['POST'])
@jwt_required()
def accept_friend_request():
    user_id = get_jwt_identity()
    data = request.get_json()
    request_id = data.get('request_id')
    
    if not request_id:
        return jsonify({"error": "request_id is required"}), 400
    
    current_app.logger.debug(f'Accepting friend request {request_id} by user {user_id}')
    
    friendship = Friendship.query.get_or_404(request_id)
    
    if str(friendship.friend_id) != str(user_id):
        current_app.logger.warning(f'Unauthorized accept attempt by user {user_id} for request {request_id}')
        return jsonify({"error": "Not authorized"}), 403
        
    # Update original request to accepted
    friendship.status = 'accepted'
    
    # Create reciprocal friendship
    reciprocal_friendship = Friendship(
        user_id=friendship.friend_id,  # Original receiver is now requester
        friend_id=friendship.user_id,  # Original requester is now receiver
        status='accepted'  # Immediately set to accepted
    )
    
    db.session.add(reciprocal_friendship)
    db.session.commit()
    
    current_app.logger.debug(f'Friend request {request_id} accepted and reciprocal friendship created')
    return jsonify({"message": "Friend request accepted"})

@bp.route('/', methods=['GET'])
@jwt_required()
def get_friends():
    user_id = get_jwt_identity()
    current_app.logger.debug(f'Getting friends for user_id: {user_id}')
    
    # Get all accepted friendships
    friends = Friendship.query.filter(
        (Friendship.user_id == user_id) &
        (Friendship.status == 'accepted')
    ).all()
    
    current_app.logger.debug(f'Found {len(friends)} friends')
    
    friend_list = []
    for friendship in friends:
        # Determine which id in the friendship is the friend's id
        friend_id = friendship.friend_id if friendship.user_id == int(user_id) else friendship.user_id
        friend = User.query.get(friend_id)
        
        if friend:
            friend_list.append({
                "user_id": int(user_id),
                "friend_id": friend.id,
                "username": friend.username,
                "created_at": friendship.created_at.isoformat()
            })
    
    return jsonify({
        "friends": friend_list,
        "total": len(friend_list)
    }) 

@bp.route('/pending', methods=['GET'])
@jwt_required()
def get_pending_requests():
    user_id = get_jwt_identity()
    current_app.logger.debug(f'Getting pending friend requests for user_id: {user_id}')
    
    # Get pending requests where the user is the receiver
    pending_requests = Friendship.query.filter_by(
        friend_id=user_id,
        status='pending'
    ).all()
    
    current_app.logger.debug(f'Found {len(pending_requests)} pending requests')
    
    requests_list = []
    for request in pending_requests:
        current_app.logger.debug(f'Processing pending request: {request.status}')
        # Get the requester's info
        requester = User.query.get(request.user_id)
        if requester:
            requests_list.append({
                "request_id": request.id,
                "from_user": {
                    "id": requester.id,
                    "username": requester.username
                },
                "created_at": request.created_at.isoformat()
            })
    
    return jsonify({
        "pending_requests": requests_list,
        "total": len(requests_list)
    }) 

@bp.route('/reject', methods=['DELETE'])
@jwt_required()
def reject_friend_request():
    user_id = get_jwt_identity()
    data = request.get_json()
    request_id = data.get('request_id')
    
    if not request_id:
        return jsonify({"error": "request_id is required"}), 400
    
    current_app.logger.debug(f'Rejecting friend request {request_id} by user {user_id}')
    
    friendship = Friendship.query.get_or_404(request_id)
    
    # Verify the user is the recipient of the request
    if str(friendship.friend_id) != str(user_id):
        current_app.logger.warning(f'Unauthorized rejection attempt by user {user_id} for request {request_id}')
        return jsonify({"error": "Not authorized"}), 403
    
    # Delete the friendship request
    db.session.delete(friendship)
    db.session.commit()
    
    current_app.logger.debug(f'Friend request {request_id} deleted successfully')
    return jsonify({"message": "Friend request rejected and deleted"}) 