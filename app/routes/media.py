from flask import Blueprint, request, jsonify, current_app, send_from_directory
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.media import Media, Comment
from app.models.user import User
from app.models.friendship import Friendship
from app.utils.file_handler import save_file
from app import db
import os

bp = Blueprint('media', __name__, url_prefix='/api/media')

@bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_media():
    user_id = get_jwt_identity()
    
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # Determine file type
    file_type = 'image' if file.content_type.startswith('image/') else 'video'
    
    current_app.logger.debug(f'Uploading {file_type} for user {user_id}')
    
    # Save file and get filename
    filename = save_file(file, file_type)
    if not filename:
        return jsonify({"error": "Invalid file type"}), 400

    # Create media record
    media = Media(
        user_id=user_id,
        media_type=file_type,
        file_path=filename,
        storage_type='local'
    )
    
    db.session.add(media)
    db.session.commit()
    
    return jsonify({
        "message": "File uploaded successfully",
        "media_id": media.id,
        "file_path": filename
    }), 201

@bp.route('/<int:media_id>', methods=['GET'])
@jwt_required()
def get_media(media_id):
    user_id = get_jwt_identity()
    current_app.logger.debug(f'Getting media {media_id}')
    
    media = Media.query.get_or_404(media_id)
    user = User.query.get(media.user_id)
    
    return jsonify({
        "created_at": media.created_at.isoformat(),
        "id": media.id,
        "media_type": media.media_type,
        "user": {
            "id": user.id,
            "username": user.username
        },
        "view_url": f"/api/media/{media.id}/view"
    })

@bp.route('/<int:media_id>', methods=['DELETE'])
@jwt_required()
def delete_media(media_id):
    user_id = get_jwt_identity()
    current_app.logger.debug(f'Attempting to delete media {media_id} by user {user_id}')
    
    # Get the media record
    media = Media.query.get_or_404(media_id)
    
    # Check if user owns this media
    if str(media.user_id) != str(user_id):
        current_app.logger.warning(f'Unauthorized deletion attempt of media {media_id} by user {user_id}')
        return jsonify({"error": "Unauthorized"}), 403
    
    # Delete file from filesystem
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], media.file_path)
    if os.path.exists(file_path):
        os.remove(file_path)
    
    # Delete database record
    db.session.delete(media)
    db.session.commit()
    
    current_app.logger.debug(f'Media {media_id} deleted successfully')
    return jsonify({"message": "Media deleted successfully"})

@bp.route('/', methods=['GET'])
@jwt_required()
def get_all_media():
    user_id = get_jwt_identity()
    current_app.logger.debug(f'Getting all media for user {user_id}')
    
    # Get all media records for user, newest first
    media_items = Media.query.filter_by(user_id=user_id)\
                            .order_by(Media.created_at.desc())\
                            .all()
    
    media_list = []
    for media in media_items:
        media_list.append({
            "id": media.id,
            "media_type": media.media_type,
            "file_path": media.file_path,
            "created_at": media.created_at.isoformat(),
            "url": f"/api/media/{media.id}"
        })
    
    current_app.logger.debug(f'Found {len(media_list)} media items')
    
    return jsonify({
        "media": media_list,
        "total": len(media_list)
    })

@bp.route('/<int:media_id>/view', methods=['GET'])
@jwt_required()
def view_media(media_id):
    user_id = get_jwt_identity()
    current_app.logger.debug(f'Attempting to view media {media_id} by user {user_id}')
    
    media = Media.query.get_or_404(media_id)
    
    # Check if user has access to this media
    if str(media.user_id) != str(user_id):
        current_app.logger.warning(f'Unauthorized view attempt of media {media_id} by user {user_id}')
        return jsonify({"error": "Unauthorized"}), 403
    
    return send_from_directory(
        current_app.config['UPLOAD_FOLDER'],
        media.file_path
    )

@bp.route('/feed', methods=['GET'])
@jwt_required()
def get_media_feed():
    user_id = get_jwt_identity()
    
    # Get pagination parameters from query string
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)  # Load 10 items at a time
    
    current_app.logger.debug(f'Getting media feed page {page} for user {user_id}')
    
    # Get paginated media items
    pagination = Media.query\
        .order_by(Media.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    media_list = []
    for media in pagination.items:
        media_list.append({
            "id": media.id,
            "media_type": media.media_type,
            "view_url": f"/api/media/{media.id}/view",
            "created_at": media.created_at.isoformat(),
            "user": {
                "id": media.user_id,
                "username": User.query.get(media.user_id).username
            }
        })
    
    return jsonify({
        "media": media_list,
        "total": pagination.total,
        "pages": pagination.pages,
        "current_page": page,
        "has_next": pagination.has_next,
        "has_prev": pagination.has_prev,
        "next_page": f"/api/media/feed?page={page+1}" if pagination.has_next else None,
        "prev_page": f"/api/media/feed?page={page-1}" if pagination.has_prev else None
    })

# Comment routes
@bp.route('/<int:media_id>/comments', methods=['POST'])
@jwt_required()
def add_comment(media_id):
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data or 'content' not in data:
        return jsonify({"error": "Content is required"}), 400
        
    media = Media.query.get_or_404(media_id)
    
    comment = Comment(
        user_id=user_id,
        media_id=media_id,
        content=data['content']
    )
    
    db.session.add(comment)
    db.session.commit()
    
    user = User.query.get(user_id)
    
    return jsonify({
        "id": comment.id,
        "content": comment.content,
        "created_at": comment.created_at.isoformat(),
        "user": {
            "id": user.id,
            "username": user.username
        }
    }), 201

@bp.route('/<int:media_id>/comments', methods=['GET'])
@jwt_required()
def get_comments(media_id):
    Media.query.get_or_404(media_id)  # Verify media exists
    
    comments = Comment.query\
        .filter_by(media_id=media_id)\
        .order_by(Comment.created_at.desc())\
        .all()
    
    comment_list = []
    for comment in comments:
        user = User.query.get(comment.user_id)
        comment_list.append({
            "id": comment.id,
            "content": comment.content,
            "created_at": comment.created_at.isoformat(),
            "user": {
                "id": user.id,
                "username": user.username
            }
        })
    
    return jsonify({
        "comments": comment_list,
        "total": len(comment_list)
    })

@bp.route('/comments/<int:comment_id>', methods=['DELETE'])
@jwt_required()
def delete_comment(comment_id):
    user_id = get_jwt_identity()
    comment = Comment.query.get_or_404(comment_id)
    
    if str(comment.user_id) != str(user_id):
        return jsonify({"error": "Not authorized"}), 403
        
    db.session.delete(comment)
    db.session.commit()
    
    return jsonify({"message": "Comment deleted successfully"})

@bp.route('/friends/feed', methods=['GET'])
@jwt_required()
def get_friends_media_feed():
    user_id = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    current_app.logger.debug(f'Getting friends media feed for user {user_id}')
    
    # Get all friend IDs from accepted friendships
    friend_ids = db.session.query(Friendship.friend_id)\
        .filter(
            (Friendship.user_id == user_id) & 
            (Friendship.status == 'accepted')
        ).all()
    
    # Extract IDs from result tuples
    friend_ids = [f[0] for f in friend_ids]
    
    # Get media from friends
    pagination = Media.query\
        .filter(Media.user_id.in_(friend_ids))\
        .order_by(Media.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    media_list = []
    for media in pagination.items:
        user = User.query.get(media.user_id)
        media_list.append({
            "id": media.id,
            "media_type": media.media_type,
            "view_url": f"/api/media/{media.id}/view",
            "created_at": media.created_at.isoformat(),
            "user": {
                "id": user.id,
                "username": user.username
            }
        })
    
    return jsonify({
        "media": media_list,
        "total": pagination.total,
        "pages": pagination.pages,
        "current_page": page,
        "has_next": pagination.has_next,
        "has_prev": pagination.has_prev
    }) 