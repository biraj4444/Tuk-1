import os

class Config:
    # Environment Variables
    SECRET_KEY = os.environ.get('SECRET_KEY')
    DEBUG = os.environ.get('DEBUG', 'False') == 'True'
    TESTING = os.environ.get('TESTING', 'False') == 'True'
    
    # Google OAuth
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
    GOOGLE_REDIRECT_URI_CLIENT = os.environ.get('GOOGLE_REDIRECT_URI_CLIENT')
    GOOGLE_REDIRECT_URI_OWNER = os.environ.get('GOOGLE_REDIRECT_URI_OWNER')
    GOOGLE_REDIRECT_URI_ADMIN = os.environ.get('GOOGLE_REDIRECT_URI_ADMIN')
    
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = os.environ.get('SQLALCHEMY_TRACK_MODIFICATIONS', 'False') == 'True'
    
    # Razorpay Payment Gateway
    RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID')
    RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET')
    
    # Portal URLs
    CLIENT_APP_URL = os.environ.get('CLIENT_APP_URL')
    OWNER_APP_URL = os.environ.get('OWNER_APP_URL')
    ADMIN_APP_URL = os.environ.get('ADMIN_APP_URL')
    
    # V3 Advanced Features Configuration
    FEATURE_X_ENABLED = os.environ.get('FEATURE_X_ENABLED', 'False') == 'True'
    FEATURE_Y_API_KEY = os.environ.get('FEATURE_Y_API_KEY')

   # Map Tiles - For Maps (MapTiler API)
MAPTILER_KEY_SAT = os.environ.get('MAPTILER_KEY_SAT')
MAPTILER_KEY_STREET = os.environ.get('MAPTILER_KEY_STREET')

# IP Info Token - For location detection
IPINFO_TOKEN = os.environ.get('IPINFO_TOKEN')
