import os
import random
import logging
import json
import shutil
from datetime import datetime, timedelta, timezone

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

# --- Configure Database ---
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
        # This function must be called within a request context to get the IP
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
def initialize_chatbot():
    global chatbot
    if chatbot is None:
        try:
            logger.info("Initializing chatbot...")
            chatbot = create_enhanced_chatbot()
            chatbot.load_model()
            logger.info("Chatbot initialized successfully!")
        except Exception as e:
            logger.error(f"Failed to initialize chatbot: {e}", exc_info=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png'}

# ==============================================================================
#  AUTHENTICATION
# ==============================================================================
@login_manager.user_loader
def load_user(user_id):
    # Use the modern db.session.get() to avoid legacy warnings
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

@app.route('/announcements')
def announcements_page():
    awards = db.session.execute(db.select(Announcement).filter_by(is_active=True, category='Award').order_by(Announcement.date.desc())).scalars().all()
    partnerships = db.session.execute(db.select(Announcement).filter_by(is_active=True, category='Partnership').order_by(Announcement.date.desc())).scalars().all()
    other_news = db.session.execute(db.select(Announcement).filter_by(is_active=True).filter(Announcement.category.notin_(['Award', 'Partnership'])).order_by(Announcement.date.desc())).scalars().all()
    return render_template('announcements_page.html', current_page='announcements', awards=awards, partnerships=partnerships, other_news=other_news)

@app.route('/careers')
def careers_overview():
    openings = db.session.execute(db.select(JobOpening).filter_by(is_active=True).order_by(JobOpening.created_at.desc())).scalars().all()
    return render_template('careers_overview.html', current_page='careers', openings=openings)

# ... (all other static frontend routes remain unchanged)
@app.route('/about-us')
def about_details(): return render_template('about_details.html', current_page='about')
@app.route('/mission-vision')
def mission_vision(): return render_template('mission_vision.html', current_page='about')
@app.route('/services')
def services_overview(): return render_template('services_overview.html', current_page='services')
@app.route('/services/ai-machine-learning')
def services_ai(): return render_template('ai_service.html', current_page='services')
@app.route('/services/digital-transformation')
def services_digital(): return render_template('digital_services.html', current_page='services')
@app.route('/services/software-development')
def services_software(): return render_template('software_services.html', current_page='services')
@app.route('/services/cybersecurity')
def services_cybersecurity(): return render_template('cybersecurity_services.html', current_page='services')
@app.route('/portfolio/ai-logistics-platform')
def portfolio_logistics(): return render_template('portfolio_logistics.html', current_page='portfolio')
@app.route('/portfolio/cloud-migration')
def portfolio_cloud(): return render_template('portfolio_cloud.html', current_page='portfolio')
@app.route('/portfolio/secure-fintech-app')
def portfolio_fintech(): return render_template('portfolio_fintech.html', current_page='portfolio')
@app.route('/portfolio/enterprise-erp')
def portfolio_erp(): return render_template('portfolio_erp.html', current_page='portfolio')
@app.route('/apply')
def application_form(): return render_template('application_form.html', current_page='careers')
@app.route('/contact-us')
def contact_page(): return render_template('contact.html', current_page='contact')

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
    if session.get('otp_verified_email') != email:
        return jsonify({'error': 'Email not verified.'}), 403
    try:
        new_message = ContactMessage(
            first_name=form.get('firstName'), last_name=form.get('lastName'),
            email=email, message_content=form.get('message')
        )
        db.session.add(new_message)
        db.session.commit()
        log_event('CONTACT_SUBMIT', f"Message from {email}")
        
        msg = Message(f"New Contact Form Submission from {form.get('firstName')} {form.get('lastName')}", recipients=[app.config['MAIL_RECIPIENT']])
        msg.html = render_template('email/contact_notification.html', data=form)
        mail.send(msg)
        session.pop('otp_verified_email', None)

        return jsonify({'message': 'Thank you! Your message has been sent successfully.'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Contact form submission failed: {e}")
        return jsonify({'error': 'An unexpected error occurred.'}), 500

@app.route('/api/detailed-apply', methods=['POST'])
def handle_apply():
    form = request.form
    files = request.files
    email = form.get('email')
    if session.get('otp_verified_email') != email:
        return jsonify({'error': 'Email not verified.'}), 403
    
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    applicant_name = f"{form.get('firstName')}_{form.get('lastName')}"
    unique_folder_name = f"{timestamp}_{secure_filename(applicant_name)}"
    application_dir = os.path.join(app.config['UPLOAD_FOLDER'], unique_folder_name)
    os.makedirs(application_dir, exist_ok=True)
    
    attachments = []
    extra_course_cert_filename = None
    if 'extra_course_cert' in files and files['extra_course_cert'].filename != '':
        file = files['extra_course_cert']
        if allowed_file(file.filename):
            extra_course_cert_filename = secure_filename(file.filename)
            file.save(os.path.join(application_dir, extra_course_cert_filename))
            attachments.append({'path': os.path.join(application_dir, extra_course_cert_filename), 'filename': extra_course_cert_filename, 'content_type': file.content_type})

    for field_name in ['resume', 'tenth_cert', 'twelfth_cert', 'ug_cert', 'pg_cert']:
        if field_name in files and files[field_name].filename != '':
            file_storage = files[field_name]
            if allowed_file(file_storage.filename):
                filename = secure_filename(file_storage.filename)
                file_path = os.path.join(application_dir, filename)
                file_storage.save(file_path)
                attachments.append({'path': file_path, 'filename': filename, 'content_type': file_storage.content_type})

    try:
        new_application = Application(
            first_name=form.get('firstName'), last_name=form.get('lastName'),
            email=email, phone_number=form.get('phoneNumber'),
            city=form.get('city'), district=form.get('district'),
            position=form.get('position'), upload_folder=unique_folder_name,
            extra_course_name=form.get('extra_course_name'),
            extra_course_cert_filename=extra_course_cert_filename
        )
        db.session.add(new_application)
        db.session.commit()
        log_event('APPLICATION_SUBMIT', f"Application from {email} for {form.get('position')}")

        msg = Message(f"New Job Application: {form.get('position')} - {applicant_name}", recipients=[app.config['MAIL_RECIPIENT']])
        msg.html = render_template('email/application_notification.html', data=form)
        for attachment in attachments:
             with app.open_resource(attachment['path']) as fp:
                msg.attach(attachment['filename'], attachment['content_type'], fp.read())
        mail.send(msg)
        session.pop('otp_verified_email', None)

        return jsonify({'message': 'Your application has been submitted successfully.'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Job application submission failed: {e}")
        return jsonify({'error': 'An unexpected error occurred.'}), 500

@app.route('/api/chatbot', methods=['POST'])
def chatbot_response():
    if not chatbot: return jsonify({'response': 'Sorry, the AI Assistant is currently offline.'})
    response = chatbot.chat(request.json.get('message', ''))
    return jsonify(response)
    
@app.route('/api/send-otp', methods=['POST'])
def send_otp():
    data = request.get_json()
    email = data.get('email')
    if not email: return jsonify({'error': 'Email is required.'}), 400
    if not app.config.get('MAIL_USERNAME'): return jsonify({'error': 'Mail server not configured.'}), 500
    otp = str(random.randint(100000, 999999))
    session['otp'], session['otp_email'] = otp, email
    session['otp_expiry'] = (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()
    try:
        msg = Message('Your Vendhan Info Tech Verification Code', recipients=[email])
        msg.body = f'Your verification code is: {otp}'
        mail.send(msg)
        return jsonify({'message': 'Verification code sent.'})
    except Exception as e:
        logger.error(f"OTP email failed: {e}")
        return jsonify({'error': 'Could not send email.'}), 500

@app.route('/api/verify-otp', methods=['POST'])
def verify_otp():
    data = request.get_json()
    if data.get('email') != session.get('otp_email') or data.get('otp') != session.get('otp'):
        return jsonify({'error': 'Invalid code or email.'}), 400
    if datetime.now(timezone.utc) > datetime.fromisoformat(session.get('otp_expiry')):
        return jsonify({'error': 'Code has expired.'}), 400
    session['otp_verified_email'] = session.get('otp_email')
    for key in ['otp', 'otp_email', 'otp_expiry']: session.pop(key, None)
    return jsonify({'message': 'Email verified!'})

# ==============================================================================
#  ADMIN PANEL APIs
# ==============================================================================
@app.route('/api/dashboard-data', methods=['GET'])
@login_required
def get_dashboard_data():
    stats = {
        'totalApplications': db.session.scalar(db.select(db.func.count(Application.id))),
        'totalMessages': db.session.scalar(db.select(db.func.count(ContactMessage.id))),
        'totalUsers': db.session.scalar(db.select(db.func.count(AdminUser.id))),
        'totalOpenings': db.session.scalar(db.select(db.func.count(JobOpening.id)).where(JobOpening.is_active==True)),
        'totalAnnouncements': db.session.scalar(db.select(db.func.count(Announcement.id)).where(Announcement.is_active==True)),
        'totalPageViews': db.session.scalar(db.select(db.func.count(EventLog.id)).where(EventLog.event_type=='PAGE_VISIT')),
    }
    return jsonify({'stats': stats})

@app.route('/api/application/<int:app_id>', methods=['GET'])
@login_required
def get_application_details(app_id):
    app_obj = db.get_or_404(Application, app_id)
    app_dir = os.path.join(app.config['UPLOAD_FOLDER'], app_obj.upload_folder)
    files = []
    if os.path.exists(app_dir):
        files = [f for f in os.listdir(app_dir) if os.path.isfile(os.path.join(app_dir, f))]
    
    replies = [{'content': r.reply_content, 'date': r.reply_date.strftime('%Y-%m-%d %H:%M'), 'author': r.author.username} for r in app_obj.replies]

    details = {
        'id': app_obj.id, 'fullName': f"{app_obj.first_name} {app_obj.last_name}",
        'email': app_obj.email, 'phone': app_obj.phone_number,
        'location': f"{app_obj.city}, {app_obj.district}", 'position': app_obj.position,
        'date': app_obj.submission_date.strftime('%Y-%m-%d'), 'status': app_obj.status,
        'files': files, 'folder': app_obj.upload_folder, 'replies': replies,
        'extra_course_name': app_obj.extra_course_name,
        'extra_course_cert': app_obj.extra_course_cert_filename
    }
    return jsonify(details)
    
def item_to_dict(item):
    d = {}
    for c in item.__table__.columns:
        val = getattr(item, c.name)
        if isinstance(val, datetime):
            d[c.name] = val.strftime('%Y-%m-%d %H:%M:%S')
        else:
            d[c.name] = val
    return d

@app.route('/api/generic/<model_name>', methods=['GET'])
@login_required
def get_all_generic(model_name):
    models = {'jobopening': JobOpening, 'announcement': Announcement, 'eventlog': EventLog, 'application': Application, 'contactmessage': ContactMessage}
    order_cols = {'jobopening': JobOpening.created_at, 'announcement': Announcement.date, 'eventlog': EventLog.timestamp, 'application': Application.submission_date, 'contactmessage': ContactMessage.submission_date}
    if model_name not in models: return jsonify({'error': 'Invalid model'}), 404
    
    items = db.session.execute(db.select(models[model_name]).order_by(order_cols[model_name].desc())).scalars().all()
    return jsonify([item_to_dict(item) for item in items])

@app.route('/api/generic/<model_name>', methods=['POST'])
@login_required
def add_generic(model_name):
    models = {'jobopening': JobOpening, 'announcement': Announcement}
    if model_name not in models: return jsonify({'error': 'Invalid model'}), 404
    data = request.get_json(); data.pop('id', None)
    try:
        new_item = models[model_name](**data)
        db.session.add(new_item)
        db.session.commit()
        log_event(f'ADMIN_ADD_{model_name.upper()}', f"Added: {data.get('title', '')}")
        return jsonify({'message': f'{model_name.capitalize()} added successfully.', 'item': item_to_dict(new_item)}), 201
    except Exception as e:
        db.session.rollback(); return jsonify({'error': str(e)}), 500

@app.route('/api/generic/<model_name>/<int:item_id>', methods=['PUT'])
@login_required
def update_generic(model_name, item_id):
    models = {'jobopening': JobOpening, 'announcement': Announcement}
    if model_name not in models: return jsonify({'error': 'Invalid model'}), 404
    item = db.get_or_404(models[model_name], item_id)
    data = request.get_json()
    try:
        for key, value in data.items():
            if hasattr(item, key) and key not in ['id', 'created_at', 'submission_date', 'date', 'timestamp']: setattr(item, key, value)
        db.session.commit()
        log_event(f'ADMIN_UPDATE_{model_name.upper()}', f"Updated ID {item_id}: {data.get('title', '')}")
        return jsonify({'message': f'{model_name.capitalize()} updated successfully.', 'item': item_to_dict(item)})
    except Exception as e:
        db.session.rollback(); return jsonify({'error': str(e)}), 500

@app.route('/api/generic/<model_name>/<int:item_id>', methods=['DELETE'])
@login_required
def delete_generic(model_name, item_id):
    models = {'jobopening': JobOpening, 'announcement': Announcement}
    if model_name not in models: return jsonify({'error': 'Invalid model'}), 404
    item = db.get_or_404(models[model_name], item_id)
    title = getattr(item, 'title', f"ID {item_id}")
    try:
        db.session.delete(item)
        db.session.commit()
        log_event(f'ADMIN_DELETE_{model_name.upper()}', f"Deleted: {title}")
        return jsonify({'message': f'{model_name.capitalize()} deleted successfully.'})
    except Exception as e:
        db.session.rollback(); return jsonify({'error': str(e)}), 500

@app.route('/api/application/update-status', methods=['POST'])
@login_required
def update_application_status():
    data = request.get_json()
    app_obj = db.get_or_404(Application, data.get('id'))
    app_obj.status = data.get('status')
    db.session.commit()
    log_event('ADMIN_STATUS_UPDATE', f"Application ID {app_obj.id} status changed to {app_obj.status}")
    return jsonify({'message': f'Status updated'}), 200

@app.route('/api/reply', methods=['POST'])
@login_required
def handle_reply():
    data, item_type, item_id, content = request.get_json(), request.json.get('type'), request.json.get('id'), request.json.get('content')
    try:
        if item_type == 'application':
            item = db.get_or_404(Application, item_id); item.status = 'Replied'
            subject = f"Update on your application for {item.position} at Vendhan Info Tech"
            new_reply = AdminReply(reply_content=content, application=item, author_id=current_user.id)
        elif item_type == 'message':
            item = db.get_or_404(ContactMessage, item_id); item.status = 'Replied'
            subject = f"Re: Your inquiry to Vendhan Info Tech"
            new_reply = AdminReply(reply_content=content, message=item, author_id=current_user.id)
        else: return jsonify({'error': 'Invalid item type.'}), 400
        
        db.session.add(new_reply); db.session.commit()
        log_event(f'ADMIN_REPLY_{item_type.upper()}', f"Replied to ID {item_id}")
        
        msg = Message(subject, recipients=[item.email], body=content); mail.send(msg)
        return jsonify({'message': 'Reply sent!'})
    except Exception as e:
        db.session.rollback(); return jsonify({'error': f'Could not send reply: {e}'}), 500

@app.route('/download/<path:folder>/<path:filename>')
@login_required
def download_file(folder, filename):
    return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER'], folder), filename, as_attachment=True)

@app.route('/api/item/delete/<item_type>/<int:item_id>', methods=['POST'])
@login_required
def delete_item(item_type, item_id):
    try:
        if item_type == 'application':
            item = db.get_or_404(Application, item_id)
            folder_path = os.path.join(app.config['UPLOAD_FOLDER'], item.upload_folder)
            if os.path.exists(folder_path): shutil.rmtree(folder_path)
        elif item_type == 'message':
            item = db.get_or_404(ContactMessage, item_id)
        else: return jsonify({'error': 'Invalid item type'}), 400
        
        db.session.delete(item); db.session.commit()
        log_event(f'ADMIN_DELETE_CONTACT/{item_type.upper()}', f"Deleted ID {item_id}")
        return jsonify({'message': f'{item_type.capitalize()} deleted.'})
    except Exception as e:
        db.session.rollback(); return jsonify({'error': 'Error during deletion.'}), 500

# ==============================================================================
#  RUN THE APP
# ==============================================================================
if __name__ == '__main__':
    with app.app_context():
        initialize_chatbot()
    app.run(host='0.0.0.0', port=5003, debug=True)