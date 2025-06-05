import os

class Config:
    """Base configuration class."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
    DEBUG = False
    TESTING = False
    
    # Database configurations
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI', 
                                            'mysql+pymysql://root:password@localhost/sped_feedback')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # DynamoDB configurations
    DYNAMODB_REGION = os.environ.get('DYNAMODB_REGION', 'us-east-1')
    DYNAMODB_ENDPOINT = os.environ.get('DYNAMODB_ENDPOINT', None)
    
    # Vector DB settings
    VECTOR_DB_HOST = os.environ.get('VECTOR_DB_HOST', 'localhost')
    VECTOR_DB_PORT = os.environ.get('VECTOR_DB_PORT', '8000')
    
    # Graph DB settings
    GRAPH_DB_URI = os.environ.get('GRAPH_DB_URI', 'bolt://localhost:7687')
    GRAPH_DB_USER = os.environ.get('GRAPH_DB_USER', 'neo4j')
    GRAPH_DB_PASSWORD = os.environ.get('GRAPH_DB_PASSWORD', 'password')
    
    # Celery settings
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'amqp://guest:guest@localhost:5672//')
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'rpc://')


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration."""
    # Production-specific settings
    DEBUG = False
    # Use strong secret key in production
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    # Add any other production-specific settings here


# Dictionary of configurations
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
