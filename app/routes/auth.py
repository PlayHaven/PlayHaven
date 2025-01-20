from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, verify_jwt_in_request, get_jwt, set_access_cookies, get_csrf_token, unset_jwt_cookies
from app.models.user import User
from app.models.profile import Profile
from app import db
from app.models.console import PlayStation, Xbox, Steam, Nintendo
from app.utils.error_handler import handle_route_errors

bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({"error": "Email already registered"}), 400
        
    if User.query.filter_by(username=data['username']).first():
        return jsonify({"error": "Username already taken"}), 400
    
    # Create user
    user = User(
        email=data['email'],
        username=data['username'],
        first_name=data.get('first_name'),
        last_name=data.get('last_name'),
        birth_date=data.get('birth_date'),
        birth_month=data.get('birth_month'),
        birth_year=data.get('birth_year')
    )
    user.set_password(data['password'])
    
    # Create empty profile
    profile = Profile(
        user=user,
        bio="",
        links={},
        games={}
    )
    
    db.session.add(user)
    db.session.add(profile)
    db.session.commit()
    
    # Create access token
    access_token = create_access_token(identity=str(user.id))
    
    # Create response
    response = jsonify({
        "message": "User created successfully",
        "user": {
            "id": user.id,
            "email": user.email,
            "username": user.username
        }
    })
    
    # Set JWT cookie and CSRF token
    set_access_cookies(response, access_token)
    response.set_cookie(
        'csrf_token',
        get_csrf_token(access_token),
        httponly=False,
        samesite='None'
    )
    
    return response, 201

@bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    
    if user and user.check_password(data['password']):
        # Create access token
        access_token = create_access_token(identity=str(user.id))
        
        # Create response
        response = jsonify({
            "message": "Login successful",
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username
            }
        })
        
        # Set JWT cookie and CSRF token
        set_access_cookies(response, access_token)
        response.set_cookie(
            'csrf_token',
            get_csrf_token(access_token),
            httponly=False,  # Frontend needs to read this
            samesite='None'
        )
        
        return response, 200
        
    return jsonify({"error": "Invalid credentials"}), 401

@bp.route('/delete', methods=['DELETE'])
@jwt_required()
def delete_account():
    user_id = str(get_jwt_identity())
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    # Delete associated profile
    profile = Profile.query.filter_by(user_id=user_id).first()
    if profile:
        db.session.delete(profile)
    
    # Delete associated console accounts
    playstation = PlayStation.query.filter_by(user_id=user_id).first()
    if playstation:
        db.session.delete(playstation)
        
    xbox = Xbox.query.filter_by(user_id=user_id).first()
    if xbox:
        db.session.delete(xbox)
        
    steam = Steam.query.filter_by(user_id=user_id).first()
    if steam:
        db.session.delete(steam)
        
    nintendo = Nintendo.query.filter_by(user_id=user_id).first()
    if nintendo:
        db.session.delete(nintendo)
    
    # Delete the user
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({"message": "Account deleted successfully"}), 200

@bp.route('/verify', methods=['GET'])
@handle_route_errors
def verify_token():
    try:
        verify_jwt_in_request()
        jwt = get_jwt()
        
        exp_timestamp = jwt["exp"]
        
        user = User.query.get(jwt["sub"])
        if not user:
            return jsonify({"valid": False, "error": "User not found"}), 404
        
        access_token = create_access_token(identity=jwt["sub"])
        
        response = jsonify({
            "valid": True,
            "expires_at": exp_timestamp,
            "user_id": jwt["sub"],
            "username": user.username,
            "email": user.email
        })
        
        set_access_cookies(response, access_token)
        response.set_cookie(
            'csrf_token',
            get_csrf_token(access_token),
            httponly=False,
            samesite='None'
        )
        
        return response, 200
        
    except Exception as e:
        current_app.logger.warning(f'Token verification failed: {str(e)}')
        return jsonify({
            "valid": False,
            "error": "Invalid or expired token"
        }), 401

@bp.route('/logout', methods=['POST'])
def logout():
    response = jsonify({"message": "Successfully logged out"})
    
    # Remove JWT cookies
    unset_jwt_cookies(response)
    
    # Remove CSRF token by setting it to expire immediately
    response.set_cookie(
        'csrf_token',
        '',  # empty value
        expires=0,  # expire immediately
        httponly=False,
        samesite='None'
    )
    
    return response, 200