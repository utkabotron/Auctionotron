import os
import secrets
import hashlib
import hmac
import json
from urllib.parse import unquote
from PIL import Image
from werkzeug.utils import secure_filename
from app import app

def verify_telegram_webapp_data(init_data, bot_token):
    """
    Verify Telegram WebApp init data
    """
    try:
        # Parse the init data
        data_pairs = []
        for item in init_data.split('&'):
            if '=' in item:
                key, value = item.split('=', 1)
                if key != 'hash':
                    data_pairs.append(f"{key}={value}")
        
        # Sort by key
        data_pairs.sort()
        data_check_string = '\n'.join(data_pairs)
        
        # Get hash from init_data
        hash_value = None
        for item in init_data.split('&'):
            if item.startswith('hash='):
                hash_value = item.split('=', 1)[1]
                break
        
        if not hash_value:
            return False
        
        # Create secret key
        secret_key = hmac.new(
            b"WebAppData",
            bot_token.encode(),
            hashlib.sha256
        ).digest()
        
        # Calculate expected hash
        expected_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(hash_value, expected_hash)
    except Exception as e:
        app.logger.error(f"Error verifying Telegram data: {e}")
        return False

def parse_telegram_user_data(init_data):
    """
    Parse user data from Telegram WebApp init data
    """
    try:
        user_data = None
        for item in init_data.split('&'):
            if item.startswith('user='):
                user_json = unquote(item.split('=', 1)[1])
                user_data = json.loads(user_json)
                break
        return user_data
    except Exception as e:
        app.logger.error(f"Error parsing user data: {e}")
        return None

def allowed_file(filename):
    """Check if uploaded file is allowed"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_uploaded_image(file, max_width=1280, max_height=1280):
    """Process and resize uploaded image"""
    if not file or not allowed_file(file.filename):
        return None
    
    try:
        # Generate secure filename
        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)
        secure_name = f"{secrets.token_hex(8)}_{name}{ext}"
        
        # Open and process image
        image = Image.open(file.stream)
        
        # Convert to RGB if needed
        if image.mode in ('RGBA', 'P'):
            image = image.convert('RGB')
        
        # Resize if needed
        if image.width > max_width or image.height > max_height:
            image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
        
        # Save processed image
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_name)
        full_path = os.path.join(app.root_path, upload_path)
        image.save(full_path, optimize=True, quality=85)
        
        return secure_name
    except Exception as e:
        app.logger.error(f"Error processing image: {e}")
        return None

def format_price(amount):
    """Format price for display"""
    if amount is None:
        return "Free"
    return f"₪{int(float(amount))}"

def calculate_time_remaining(end_time):
    """Calculate time remaining for auction"""
    if not end_time:
        return None
    
    from datetime import datetime
    now = datetime.utcnow()
    if end_time <= now:
        return {"expired": True}
    
    delta = end_time - now
    hours = delta.seconds // 3600
    minutes = (delta.seconds % 3600) // 60
    seconds = delta.seconds % 60
    
    return {
        "expired": False,
        "days": delta.days,
        "hours": hours,
        "minutes": minutes,
        "seconds": seconds,
        "total_seconds": delta.total_seconds()
    }
