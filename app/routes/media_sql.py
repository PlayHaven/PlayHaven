from flask import Blueprint, request, jsonify, current_app, send_from_directory, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.media import Media, Comment
from app.models.user import User
from app.models.friendship import Friendship
from app.utils.file_handler import save_file
from app.utils.error_handler import handle_route_errors
from app import db
import os
import io

bp = Blueprint('media_sql', __name__, url_prefix='/api/media_sql')


@bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_media():
    user_id = get_jwt_identity()
    
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # Check if the file is an image
    if not file.content_type.startswith('image/'):
        return jsonify({"error": "File must be an image"}), 400

    current_app.logger.debug(f'Uploading image for user {user_id}')
    
    # Read the file data
    file_data = file.read()

    # Create media record with binary data
    media = Media(
        user_id=user_id,
        media_type='image',
        data=file_data,  # Store the image data directly
        storage_type='database'  # Indicate that the image is stored in the database
    )
    
    db.session.add(media)
    db.session.commit()
    
    return jsonify({
        "message": "Image uploaded successfully",
        "media_id": media.id
    }), 201


@bp.route('/<int:media_id>', methods=['GET'])
@jwt_required()
def get_media(media_id):
    user_id = get_jwt_identity()
    current_app.logger.debug(f'Getting media {media_id}')
    
    media = Media.query.get_or_404(media_id)
    
    return jsonify({
        "created_at": media.created_at.isoformat(),
        "id": media.id,
        "media_type": media.media_type,
        "user_id": media.user_id,
        "view_url": f"/media_sql/image/{media.id}"  # URL to retrieve the image
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
    
    # Delete database record
    db.session.delete(media)
    db.session.commit()
    
    current_app.logger.debug(f'Media {media_id} deleted successfully')
    return jsonify({"message": "Media deleted successfully"}), 200


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
            "created_at": media.created_at.isoformat(),
            "url": f"/api/media_sql/image/{media.id}"  # URL to retrieve the image
        })
    
    current_app.logger.debug(f'Found {len(media_list)} media items')
    
    return jsonify({
        "media": media_list,
        "total": len(media_list)
    })


@bp.route('/image/<int:media_id>', methods=['GET'])
@jwt_required()
def get_image(media_id):
    # Fetch the media record from the database
    media = Media.query.get_or_404(media_id)

    # Check if the media type is an image
    if media.media_type != 'image':
        return jsonify({"error": "Media is not an image"}), 400

    # Return the image data directly
    response = send_file(
        io.BytesIO(media.data),  # Convert binary data to a BytesIO object
        mimetype='image/jpeg'  # Change this if you support other image types
    )
    
    return response


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
    
    return jsonify({"message": "Comment deleted successfully"}), 200


@bp.route('/feed', methods=['GET'])
@jwt_required()
def get_media_feed():
    user_id = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    current_app.logger.debug(f'Getting media feed for user {user_id}')
    
    # Get all friend IDs from accepted friendships
    friend_ids = db.session.query(Friendship.friend_id)\
        .filter(
            (Friendship.user_id == user_id) & 
            (Friendship.status == 'accepted')
        ).all()
    
    # Extract IDs from result tuples
    friend_ids = [f[0] for f in friend_ids]
    
    # Include the user's own ID in the list
    friend_ids.append(user_id)
    
    # Get media from friends and the user
    pagination = Media.query\
        .filter(Media.user_id.in_(friend_ids))\
        .order_by(Media.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    media_list = []
    for media in pagination.items:
        media_list.append({
            "id": media.id,
            "media_type": media.media_type,
            "view_url": f"/media_sql/image/{media.id}",
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
        "has_prev": pagination.has_prev
    })