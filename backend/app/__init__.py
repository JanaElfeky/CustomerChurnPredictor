from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from dotenv import load_dotenv
import os

db = SQLAlchemy()
migrate = Migrate()


def create_app(config_name=None):
    """Application factory pattern"""
    # Load environment variables from .env file
    env_path = os.path.join(os.path.dirname(__file__), 'config', '.env')
    load_dotenv(env_path)


    app = Flask(__name__)

    # Determine config
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    # Load config from config.py
    from app.config.config import config
    app.config.from_object(config[config_name])

    print("DB URI in this run:", app.config["SQLALCHEMY_DATABASE_URI"])

    # Validate production config
    if config_name == 'production' and not app.config.get('SECRET_KEY'):
        raise ValueError("SECRET_KEY must be set in production environment")

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app)

    with app.app_context():
        db.create_all()

    # Register blueprints
    register_blueprints(app)

    # Register error handlers
    register_error_handlers(app)

    # Initialize scheduler (if enabled via config)
    from app.services.scheduler_service import init_scheduler
    init_scheduler(app)

    return app


def register_blueprints(app):
    """Register Flask blueprints"""
    # Import blueprints here to avoid circular imports
    from app.routes.prediction_routes import prediction_bp
    from app.routes.history_routes import history_bp
    from app.routes.feedback_routes import feedback_bp
    from app.routes.scheduler_routes import scheduler_bp

    app.register_blueprint(prediction_bp)
    app.register_blueprint(history_bp)
    app.register_blueprint(feedback_bp)
    app.register_blueprint(scheduler_bp)


def register_error_handlers(app):
    """Register error handlers"""

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'error': 'Resource not found',
            'message': str(error)
        }), 404

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'success': False,
            'error': 'Bad request',
            'message': str(error)
        }), 400

    @app.errorhandler(500)
    def internal_server_error(error):
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': 'An unexpected error occurred'
        }), 500

    @app.errorhandler(Exception)
    def handle_exception(error):
        app.logger.error(f'Unhandled exception: {str(error)}')
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': 'An unexpected error occurred'
        }), 500
