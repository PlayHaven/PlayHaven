from functools import wraps
from flask import jsonify, current_app

def handle_route_errors(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            current_app.logger.error(f"Route error: {str(e)}")
            return jsonify({"error": str(e)}), 500
    return decorated_function 