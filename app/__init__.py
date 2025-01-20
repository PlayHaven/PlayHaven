from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
import logging
from .config import Config
from flask_socketio import SocketIO, emit
from flask import current_app, jsonify

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
socketio = SocketIO(cors_allowed_origins="*")

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Configure CORS
    CORS(app, 
         resources={r"/api/*": {
             "origins": [
                 "http://localhost:3000",
                 "http://localhost:5001",
                 "https://playhaven-fe.onrender.com"  # Add your Render frontend URL
             ],
             "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
             "allow_headers": ["Content-Type", "Authorization", "X-CSRF-TOKEN"],
             "expose_headers": ["Content-Type", "X-CSRF-TOKEN"]
         }},
         supports_credentials=True
    )

    # Configure logging
    app.logger.setLevel(logging.DEBUG)
    # Add console handler if not already present
    if not app.logger.handlers:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        app.logger.addHandler(console_handler)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    socketio.init_app(app)

    # Import models to register them with SQLAlchemy
    from .models.user import User
    from .models.profile import Profile
    from .models.media import Media
    from .models.friendship import Friendship
    from .models.console import PlayStation, Xbox, Steam, Nintendo, Discord
    from .models.notification import Notification
    from .models.chat import ChatMessage, ChatRoom

    from .routes import auth, profile, media, friendship, chat, notifications, health
    app.register_blueprint(auth.bp)
    app.register_blueprint(profile.bp)
    app.register_blueprint(media.bp)
    app.register_blueprint(friendship.bp)
    app.register_blueprint(chat.bp)
    app.register_blueprint(notifications.bp)
    app.register_blueprint(health.bp)

    return app