from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from dotenv import load_dotenv
import os

db = SQLAlchemy()


def create_app(config_name=None):
    """Application factory pattern"""
    # Load environment variables from .env file
    load_dotenv()

    app = Flask(__name__)

    # Determine config
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    # Load config from config.py
    from app.config.config import config
    app.config.from_object(config[config_name])

    # Validate production config
    if config_name == 'production' and not app.config.get('SECRET_KEY'):
        raise ValueError("SECRET_KEY must be set in production environment")

    # Initialize extensions
    db.init_app(app)
    CORS(app)

    # Register blueprints
    register_blueprints(app)

    # Register error handlers
    register_error_handlers(app)

    return app


def register_blueprints(app):
    """Register Flask blueprints"""
    # Import blueprints here to avoid circular imports
    from app.routes.prediction_routes import prediction_bp

    app.register_blueprint(prediction_bp)
    pass


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
