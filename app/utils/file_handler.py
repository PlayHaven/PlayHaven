import os
from werkzeug.utils import secure_filename
from flask import current_app
import uuid

def allowed_file(filename, allowed_extensions):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def save_file(file, file_type):
    if file and allowed_file(file.filename, 
                           current_app.config['ALLOWED_IMAGE_EXTENSIONS'] if file_type == 'image' 
                           else current_app.config['ALLOWED_VIDEO_EXTENSIONS']):
        
        # Create unique filename
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        
        # Create upload folder if it doesn't exist
        os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        # Save file
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        
        return unique_filename
    return None 