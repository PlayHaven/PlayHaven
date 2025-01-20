from flask import Blueprint, jsonify

bp = Blueprint('health', __name__)

@bp.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200 