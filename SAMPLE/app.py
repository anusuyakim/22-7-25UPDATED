import os
import random
import logging
import json
import shutil
from datetime import datetime, timedelta, timezone
import requests

from flask import Flask, render_template, request, jsonify, url_for, session, redirect, flash, send_from_directory
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from flask_mail import Mail, Message
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_migrate import Migrate

from download_model import create_enhanced_chatbot

# --- Load Environment Variables ---
load_dotenv()

# --- Initialize Flask App and Extensions ---
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'a_very_secret_key_for_dev_only')

# --- Configure File Uploads ---
UPLOAD_FOLDER = os.path.join(app.instance_path, 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 25 * 1024 * 1024

# --- Configure Database (MODIFIED FOR RENDER POSTGRESQL) ---
if 'DATABASE_URL' in os.environ:
    # This block runs when deployed on Render
    database_url = os.environ.get('DATABASE_URL').replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    # This block runs when you are developing locally (e.g., in Codespaces)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.instance_path, 'app.db')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# --- Configure Flask-Mail ---
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'true').lower() in ['true', '1', 't']
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')
app.config['MAIL_RECIPIENT'] = os.getenv('MAIL_RECIPIENT')
mail = Mail(app)

# --- Configure Flask-Login ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = "You must be logged in to access the admin panel."
login_manager.login_message_category = "error"

# --- Set up logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==============================================================================
#  DATABASE MODELS
# ==============================================================================
class AdminUser(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    replies = db.relationship('AdminReply', backref='author', lazy=True)
    def set_password(self, password): self.password_hash = generate_password_hash(password)
    def check_password(self, password): return check_password_hash(self.password_hash, password)

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    city = db.Column(db.String(100))
    district = db.Column(db.String(100))
    position = db.Column(db.String(100), nullable=False)
    extra_course_name = db.Column(db.String(200))
    extra_course_cert_filename = db.Column(db.String(200))
    upload_folder = db.Column(db.String(300), nullable=False)
    status = db.Column(db.String(50), default='New', nullable=False)
    submission_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    replies = db.relationship('AdminReply', backref='application', lazy=True, cascade="all, delete-orphan")

class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    message_content = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default='New', nullable=False)
    submission_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    replies = db.relationship('AdminReply', backref='message', lazy=True, cascade="all, delete-orphan")

class AdminReply(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reply_content = db.Column(db.Text, nullable=False)
    reply_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    application_id = db.Column(db.Integer, db.ForeignKey('application.id'), nullable=True)
    message_id = db.Column(db.Integer, db.ForeignKey('contact_message.id'), nullable=True)
    author_id = db.Column(db.Integer, db.ForeignKey('admin_user.id'), nullable=False)

class JobOpening(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    location_type = db.Column(db.String(100), nullable=False)
    job_type = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    is_active = db.Column(db.Boolean, default=True)

class EventLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    ip_address = db.Column(db.String(45))
    event_type = db.Column(db.String(100))
    details = db.Column(db.Text)

# ==============================================================================
#  HELPER FUNCTIONS
# ==============================================================================
def log_event(event_type, details=""):
    try:
        if request:
            ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
            log = EventLog(ip_address=ip_address, event_type=event_type, details=details)
            db.session.add(log)
            db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error logging event: {e}")

def visitor_tracker():
    if request.path and not request.path.startswith(('/static', '/api', '/download', '/admin', '/favicon.ico')):
         log_event('PAGE_VISIT', f"Visited: {request.path}")

app.before_request(visitor_tracker)

chatbot = None 
def get_chatbot():
    """ Initializes the chatbot on the first request that needs it. """
    global chatbot
    if chatbot is None:
        try:
            logger.info("Initializing chatbot for the first time...")
            chatbot = create_enhanced_chatbot()
            chatbot.load_model()
            logger.info("Chatbot initialized successfully!")
        except Exception as e:
            logger.error(f"FATAL: Failed to initialize chatbot: {e}", exc_info=True)
    return chatbot

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png'}

# ==============================================================================
#  AUTHENTICATION & CLI
# ==============================================================================
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(AdminUser, int(user_id))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated: return redirect(url_for('admin_panel'))
    if request.method == 'POST':
        user = db.session.execute(db.select(AdminUser).filter_by(username=request.form.get('username'))).scalar_one_or_none()
        if user and user.check_password(request.form.get('password')):
            login_user(user)
            log_event('ADMIN_LOGIN', f"User '{user.username}' logged in.")
            return redirect(request.args.get("next") or url_for('admin_panel'))
        else:
            flash('Invalid username or password.', 'error')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    log_event('ADMIN_LOGOUT', f"User '{current_user.username}' logged out.")
    logout_user()
    return redirect(url_for('login'))

@app.cli.command("create-admin")
def create_admin():
    username = input("Enter admin username: ")
    password = input("Enter admin password: ")
    if db.session.execute(db.select(AdminUser).filter_by(username=username)).scalar_one_or_none():
        print(f"User '{username}' already exists.")
        return
    new_admin = AdminUser(username=username)
    new_admin.set_password(password)
    db.session.add(new_admin)
    db.session.commit()
    print(f"Admin user '{username}' created successfully!")

# ==============================================================================
#  FRONTEND ROUTES
# ==============================================================================
@app.route('/')
def home():
    announcements = db.session.execute(db.select(Announcement).filter_by(is_active=True).order_by(Announcement.date.desc()).limit(3)).scalars().all()
    return render_template('index.html', current_page='home', announcements=announcements)

# ... (all other frontend routes are correct and unchanged) ...

# ==============================================================================
#  ADMIN PANEL ROUTE
# ==============================================================================
@app.route('/admin')
@login_required
def admin_panel():
    return render_template('admin.html')

# ==============================================================================
#  API & FORM HANDLING
# ==============================================================================
@app.route('/api/contact', methods=['POST'])
def handle_contact():
    form = request.form
    email = form.get('email')
    if not app.config.get('MAIL_USERNAME'):
        logger.warning("Mail not configured. Skipping email notification.")
    elif session.get('otp_verified_email') != email:
        return jsonify({'error': 'Email not verified.'}), 403
    try:
        new_message = ContactMessage(
            first_name=form.get('firstName'), last_name=form.get('lastName'),
            email=email, message_content=form.get('message')
        )
        db.session.add(new_message)
        db.session.commit()
        log_event('CONTACT_SUBMIT', f"Message from {email}")
        
        if app.config.get('MAIL_USERNAME'):
            msg = Message(f"New Contact Form Submission from {form.get('firstName')} {form.get('lastName')}", recipients=[app.config['MAIL_RECIPIENT']])
            msg.html = render_template('email/contact_notification.html', data=form)
            mail.send(msg)
        
        session.pop('otp_verified_email', None)
        return jsonify({'message': 'Thank you! Your message has been sent successfully.'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Contact form submission failed: {e}")
        return jsonify({'error': 'An unexpected error occurred.'}), 500

# ... (all other API and form handling routes are correct and unchanged) ...
@app.route('/api/live-updates')
def live_updates():
    weather_key = os.getenv('OPENWEATHER_API_KEY')
    news_key = os.getenv('NEWS_API_KEY')
    weather_data, news_data = None, None
    lat = request.args.get('lat')
    lon = request.args.get('lon')

    if weather_key:
        try:
            if lat and lon:
                weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={weather_key}&units=metric"
            else:
                weather_url = f"https://api.openweathermap.org/data/2.5/weather?q=Oddanchatram,IN&appid={weather_key}&units=metric"
            response = requests.get(weather_url, timeout=5)
            response.raise_for_status()
            weather_data = response.json()
        except Exception as e:
            logger.error(f"Could not fetch weather data: {e}"); weather_data = {"error": "Weather data is currently unavailable."}
    
    if news_key:
        try:
            news_url = f"https://newsapi.org/v2/everything?q=technology&language=en&sortBy=publishedAt&apiKey={news_key}&pageSize=10"
            response = requests.get(news_url, timeout=5)
            response.raise_for_status()
            news_data = response.json()
        except Exception as e:
            logger.error(f"Could not fetch news data: {e}"); news_data = {"error": "News data is currently unavailable."}

    return jsonify({'weather': weather_data, 'news': news_data})

# ==============================================================================
#  RUN THE APP
# ==============================================================================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=True)