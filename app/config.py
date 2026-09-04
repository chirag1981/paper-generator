import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'exam-paper-ai-dev-secret-key-9876543210')
    UPLOAD_FOLDER = str(BASE_DIR / os.environ.get('UPLOAD_FOLDER', 'uploads'))
    EXPORT_FOLDER = str(BASE_DIR / os.environ.get('EXPORT_FOLDER', 'exports'))
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 32 * 1024 * 1024)) # 32 MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'bmp', 'pdf'}
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False

class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    WTF_CSRF_ENABLED = False

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True

config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
