from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.profile import Profile
from app.models.user import User
from app import db
from app.models.console import PlayStation, Xbox, Steam, Nintendo, Discord
from app.models.friendship import Friendship

bp = Blueprint('profile', __name__, url_prefix='/api/profile')

@bp.route('/', methods=['GET'])
@jwt_required()
def get_profile():
    user_id = get_jwt_identity()
    current_app.logger.debug(f'Getting profile for user_id: {user_id}')
    
    profile = Profile.query.filter_by(user_id=user_id).first()
    
    if not profile:
        current_app.logger.error(f'Profile not found for user_id: {user_id}')
        return jsonify({"error": "Profile not found"}), 404
    
    # Users I'm following (I added them)
    following = Friendship.query.filter_by(
        user_id=user_id, 
        status='accepted'
    ).all()
    
    # Users following me (they added me)
    followers = Friendship.query.filter_by(
        friend_id=user_id, 
        status='accepted'
    ).all()
    
    # Convert to lists of user details
    following_list = []
    for friend in following:
        friend_user = User.query.get(friend.friend_id)
        if friend_user:
            following_list.append({
                "user_id": friend_user.id,
                "username": friend_user.username
            })
    
    followers_list = []
    for friend in followers:
        friend_user = User.query.get(friend.user_id)
        if friend_user:
            followers_list.append({
                "user_id": friend_user.id,
                "username": friend_user.username
            })
    
    discord = Discord.query.filter_by(user_id=user_id).first()
    
    # Get console information
    ps = PlayStation.query.filter_by(user_id=user_id).first()
    xbox = Xbox.query.filter_by(user_id=user_id).first()
    steam = Steam.query.filter_by(user_id=user_id).first()
    nintendo = Nintendo.query.filter_by(user_id=user_id).first()
        
    return jsonify({
        "bio": profile.bio,
        "discord": discord.discord_username if discord else None,
        "links": profile.links,
        "games": profile.games,
        "following": following_list,
        "followers": followers_list,
        "consoles": {
            "playstation": {"psn_username": ps.psn_username} if ps else None,
            "xbox": {"xbox_gamertag": xbox.xbox_gamertag} if xbox else None,
            "steam": { "steam_username": steam.steam_username } if steam else None,
            "nintendo": {"friend_code": nintendo.friend_code} if nintendo else None
        }
    })

@bp.route('/bio', methods=['PUT'])
@jwt_required()
def update_bio():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    profile = Profile.query.filter_by(user_id=user_id).first()
    if not profile:
        profile = Profile(user_id=user_id)
        db.session.add(profile)
    
    profile.bio = data.get('bio', profile.bio)
    db.session.commit()
    return jsonify({"message": "Bio updated successfully"})

@bp.route('/links', methods=['PUT'])
@jwt_required()
def update_links():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    profile = Profile.query.filter_by(user_id=user_id).first()
    if not profile:
        profile = Profile(user_id=user_id)
        db.session.add(profile)
    
    profile.links = data.get('links', profile.links)
    db.session.commit()
    return jsonify({"message": "Links updated successfully"})

@bp.route('/games', methods=['PUT'])
@jwt_required()
def update_games():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    profile = Profile.query.filter_by(user_id=user_id).first()
    if not profile:
        profile = Profile(user_id=user_id)
        db.session.add(profile)
    
    profile.games = data.get('games', profile.games)
    db.session.commit()
    return jsonify({"message": "Games updated successfully"})

@bp.route('/consoles', methods=['GET'])
@jwt_required()
def get_consoles():
    user_id = get_jwt_identity()
    
    ps = PlayStation.query.filter_by(user_id=user_id).first()
    xbox = Xbox.query.filter_by(user_id=user_id).first()
    steam = Steam.query.filter_by(user_id=user_id).first()
    nintendo = Nintendo.query.filter_by(user_id=user_id).first()
    
    return jsonify({
        "playstation": {"psn_username": ps.psn_username} if ps else None,
        "xbox": {"xbox_gamertag": xbox.xbox_gamertag} if xbox else None,
        "steam": {
            "steam_username": steam.steam_username,
            "discord_username": steam.discord_username
        } if steam else None,
        "nintendo": {"friend_code": nintendo.friend_code} if nintendo else None
    })

@bp.route('/consoles/playstation', methods=['PUT'])
@jwt_required()
def update_playstation():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    ps = PlayStation.query.filter_by(user_id=user_id).first()
    if not ps:
        ps = PlayStation(user_id=user_id)
        db.session.add(ps)
    
    ps.psn_username = data.get('psn_username', ps.psn_username)
    db.session.commit()
    return jsonify({"message": "PlayStation info updated successfully"})

@bp.route('/consoles/xbox', methods=['PUT'])
@jwt_required()
def update_xbox():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    xbox = Xbox.query.filter_by(user_id=user_id).first()
    if not xbox:
        xbox = Xbox(user_id=user_id)
        db.session.add(xbox)
    
    xbox.xbox_gamertag = data.get('xbox_gamertag', xbox.xbox_gamertag)
    db.session.commit()
    return jsonify({"message": "Xbox info updated successfully"})

@bp.route('/consoles/steam', methods=['PUT'])
@jwt_required()
def update_steam():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    steam = Steam.query.filter_by(user_id=user_id).first()
    if not steam:
        steam = Steam(user_id=user_id)
        db.session.add(steam)
    
    steam.steam_username = data.get('steam_username', steam.steam_username)
    db.session.commit()
    return jsonify({"message": "Steam info updated successfully"})

@bp.route('/consoles/nintendo', methods=['PUT'])
@jwt_required()
def update_nintendo():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    nintendo = Nintendo.query.filter_by(user_id=user_id).first()
    if not nintendo:
        nintendo = Nintendo(user_id=user_id)
        db.session.add(nintendo)
    
    nintendo.friend_code = data.get('friend_code', nintendo.friend_code)
    db.session.commit()
    return jsonify({"message": "Nintendo info updated successfully"}) 

@bp.route('/discord', methods=['PUT'])
@jwt_required()
def update_discord():
    user_id = get_jwt_identity()
    data = request.get_json()
    discord = Discord.query.filter_by(user_id=user_id).first()
    discord.discord_username = data.get('discord_username', discord.discord_username)
    db.session.commit()
    return jsonify({"message": "Discord info updated successfully"})
