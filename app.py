import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.DEBUG)
load_dotenv()

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Enable CORS for all routes with credentials support (required for session cookies)
# Explicitly allow our custom header for Telegram WebApp auth passthrough
CORS(
    app,
    supports_credentials=True,
    allow_headers=[
        'Content-Type',
        'X-Telegram-Init-Data',
    ],
    expose_headers=['Set-Cookie']
)

# configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///auction.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Session cookie settings (tunable via env for Telegram WebView / HTTPS)
# When serving via HTTPS/ngrok inside Telegram, set ENABLE_CROSS_SITE_COOKIES=1
# and optionally SESSION_COOKIE_SECURE=1 in your environment.
app.config['SESSION_COOKIE_SAMESITE'] = (
    'None' if os.environ.get('ENABLE_CROSS_SITE_COOKIES', '').lower() in ('1', 'true', 'yes') else 'Lax'
)
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('SESSION_COOKIE_SECURE', '').lower() in ('1', 'true', 'yes')

# File upload configuration
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# initialize the app with the extension
db.init_app(app)

with app.app_context():
    # Make sure to import the models here or their tables won't be created
    import models  # noqa: F401
    
    # Create upload directory if it doesn't exist
    upload_dir = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'])
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    
    db.create_all()

# Import routes after app initialization
from routes import *  # noqa: F401
