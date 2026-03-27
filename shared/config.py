import os

class Config:
    # Environment Variables
    SECRET_KEY = os.environ.get('SECRET_KEY')
    DEBUG = os.environ.get('DEBUG', 'False') == 'True'
    TESTING = os.environ.get('TESTING', 'False') == 'True'
    
    # Google OAuth
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
    
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = os.environ.get('SQLALCHEMY_TRACK_MODIFICATIONS', 'False') == 'True'
    
    # V3 Advanced Features Configuration
    FEATURE_X_ENABLED = os.environ.get('FEATURE_X_ENABLED', 'False') == 'True'
    FEATURE_Y_API_KEY = os.environ.get('FEATURE_Y_API_KEY')
    
    # Additional configurations can go here
