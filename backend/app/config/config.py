import os


class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY')

    # SQLAlchemy configuration
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False

    # Database
    # Support both DATABASE_URL and Supabase connection strings
    database_url = os.environ.get(
        'DATABASE_URL') or 'sqlite:///churn_predictor.db'

    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)

    SQLALCHEMY_DATABASE_URI = database_url

    # Connection pool settings for PostgreSQL/Supabase
    if database_url.startswith('postgresql://'):
        SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_size': 10,
            'pool_recycle': 3600,
            'pool_pre_ping': True,
            'max_overflow': 20,
            'connect_args': {
                'connect_timeout': 10,
            }
        }

    # File upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = os.path.join(
        os.path.dirname(
            os.path.dirname(__file__)),
        'uploads')

    # Model settings
    MODEL_FOLDER = os.path.join(
        os.path.dirname(
            os.path.dirname(__file__)),
        'models')

    # Scheduler settings
    ENABLE_SCHEDULER = os.environ.get(
        'ENABLE_SCHEDULER', 'False').lower() == 'true'
    RETRAINING_INTERVAL_HOURS = float(
        os.environ.get('RETRAINING_INTERVAL_HOURS', '24'))


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    SQLALCHEMY_ECHO = True


class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = False
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False

    # Override to require SECRET_KEY from environment in production
    SECRET_KEY = os.environ.get('SECRET_KEY')


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
