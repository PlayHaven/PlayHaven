from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
import logging
from .config import Config

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

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

    # Import models to register them with SQLAlchemy
    from .models.user import User
    from .models.profile import Profile
    from .models.media import Media
    from .models.friendship import Friendship
    from .models.console import PlayStation, Xbox, Steam, Nintendo, Discord

    from .routes import auth, profile, media, friendship
    app.register_blueprint(auth.bp)
    app.register_blueprint(profile.bp)
    app.register_blueprint(media.bp)
    app.register_blueprint(friendship.bp)

    return app