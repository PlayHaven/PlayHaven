from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
import os
from app.models.media import Media
from app import db

bp = Blueprint('media', __name__, url_prefix='/api/media')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_media():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
        
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join('uploads', filename)
        file.save(file_path)
        
        media = Media(
            profile_id=get_jwt_identity(),
            media_type='video' if filename.rsplit('.', 1)[1].lower() in ['mp4', 'mov'] else 'photo',
            file_path=file_path
        )
        db.session.add(media)
        db.session.commit()
        
        return jsonify({"message": "Media uploaded successfully"}), 201
        
    return jsonify({"error": "File type not allowed"}), 400 