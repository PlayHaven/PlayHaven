from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app.models.user import User
from app.models.profile import Profile
from app import db
from app.models.console import PlayStation, Xbox, Steam, Nintendo

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
    
    return jsonify({"message": "User created successfully"}), 201

@bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    
    if user and user.check_password(data['password']):
        access_token = create_access_token(identity=str(user.id))
        return jsonify({"token": access_token}), 200
        
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