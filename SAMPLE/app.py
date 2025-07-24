import os
import random
import logging
import json
import shutil
from datetime import datetime, timedelta

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
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload size

# --- Configure Database (NEW) ---
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

# --- Configure Flask-Login (NEW) ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # Redirect to this page if user is not logged in
login_manager.login_message = "You must be logged in to access the admin panel."
login_manager.login_message_category = "error"

# --- Set up logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==============================================================================
#  DATABASE MODELS (NEW)
# ==============================================================================
class AdminUser(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    city = db.Column(db.String(100))
    district = db.Column(db.String(100))
    position = db.Column(db.String(100), nullable=False)
    upload_folder = db.Column(db.String(300), nullable=False) # Path to the unique folder
    status = db.Column(db.String(50), default='New', nullable=False)
    submission_date = db.Column(db.DateTime, default=datetime.utcnow)
    replies = db.relationship('AdminReply', backref='application', lazy=True, cascade="all, delete-orphan")

class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    message_content = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default='New', nullable=False)
    submission_date = db.Column(db.DateTime, default=datetime.utcnow)
    replies = db.relationship('AdminReply', backref='message', lazy=True, cascade="all, delete-orphan")

class AdminReply(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reply_content = db.Column(db.Text, nullable=False)
    reply_date = db.Column(db.DateTime, default=datetime.utcnow)
    application_id = db.Column(db.Integer, db.ForeignKey('application.id'), nullable=True)
    message_id = db.Column(db.Integer, db.ForeignKey('contact_message.id'), nullable=True)
    author_id = db.Column(db.Integer, db.ForeignKey('admin_user.id'), nullable=False)

# --- Chatbot Initialization ---
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

# --- Helper function ---
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'pdf', 'doc', 'docx'}

# ==============================================================================
#  AUTHENTICATION ROUTES & USER LOADER (NEW)
# ==============================================================================
@login_manager.user_loader
def load_user(user_id):
    return AdminUser.query.get(int(user_id))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin_panel'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = AdminUser.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('admin_panel'))
        else:
            flash('Invalid username or password.', 'error')
    return render_template('login.html') # You will need to create this simple login page

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# --- Command to create admin user ---
@app.cli.command("create-admin")
def create_admin():
    """Creates the initial admin user."""
    username = input("Enter admin username: ")
    password = input("Enter admin password: ")
    existing_user = AdminUser.query.filter_by(username=username).first()
    if existing_user:
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
def home(): return render_template('index.html', current_page='home')
# ... (all your other frontend routes remain unchanged)
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
@app.route('/announcements')
def announcements_page(): return render_template('announcements_page.html', current_page='announcements')
@app.route('/careers')
def careers_overview(): return render_template('careers_overview.html', current_page='careers')
@app.route('/apply')
def application_form(): return render_template('application_form.html', current_page='careers')
@app.route('/contact-us')
def contact_page(): return render_template('contact.html', current_page='contact')

# ==============================================================================
#  ADMIN PANEL ROUTE (NEW)
# ==============================================================================
@app.route('/admin')
@login_required
def admin_panel():
    return render_template('admin.html')

# ==============================================================================
#  EXISTING API & FORM HANDLING ROUTES (MODIFIED)
# ==============================================================================
@app.route('/api/contact', methods=['POST'])
def handle_contact():
    form = request.form
    email = form.get('email')
    if session.get('otp_verified_email') != email:
        return jsonify({'error': 'Email not verified. Please complete the verification step.'}), 403
    try:
        # Save to database
        new_message = ContactMessage(
            first_name=form.get('firstName'),
            last_name=form.get('lastName'),
            email=email,
            message_content=form.get('message')
        )
        db.session.add(new_message)
        db.session.commit()

        # Send email notification
        msg = Message(
            f"New Contact Form Submission from {form.get('firstName')} {form.get('lastName')}",
            recipients=[app.config['MAIL_RECIPIENT']]
        )
        msg.html = render_template('email/contact_notification.html', data=form)
        mail.send(msg)
        
        session.pop('otp_verified_email', None)
        return jsonify({'message': 'Thank you! Your message has been sent successfully.'})
    except Exception as e:
        logger.error(f"Contact form submission failed: {e}")
        db.session.rollback()
        return jsonify({'error': 'An unexpected error occurred. Please try again later.'}), 500

@app.route('/api/detailed-apply', methods=['POST'])
def handle_apply():
    form = request.form
    files = request.files
    email = form.get('email')
    if session.get('otp_verified_email') != email:
        return jsonify({'error': 'Email not verified. Please complete the verification step.'}), 403
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    applicant_name = f"{form.get('firstName')}_{form.get('lastName')}"
    unique_folder_name = f"{timestamp}_{secure_filename(applicant_name)}"
    application_dir = os.path.join(app.config['UPLOAD_FOLDER'], unique_folder_name)
    os.makedirs(application_dir, exist_ok=True)
    
    attachments = []
    for field_name, file_storage in files.items():
        if file_storage and allowed_file(file_storage.filename):
            filename = secure_filename(file_storage.filename)
            file_path = os.path.join(application_dir, filename)
            file_storage.save(file_path)
            attachments.append({'path': file_path, 'filename': filename, 'content_type': file_storage.content_type})

    try:
        # Save application to database
        new_application = Application(
            first_name=form.get('firstName'),
            last_name=form.get('lastName'),
            email=email,
            phone_number=form.get('phoneNumber'),
            city=form.get('city'),
            district=form.get('district'),
            position=form.get('position'),
            upload_folder=unique_folder_name # Store relative path to the folder
        )
        db.session.add(new_application)
        db.session.commit()
        
        # Send email notification
        msg = Message(f"New Job Application: {form.get('position')} - {applicant_name}", recipients=[app.config['MAIL_RECIPIENT']])
        msg.html = render_template('email/application_notification.html', data=form)
        for attachment in attachments:
            with app.open_resource(attachment['path']) as fp:
                msg.attach(attachment['filename'], attachment['content_type'], fp.read())
        mail.send(msg)
        
        session.pop('otp_verified_email', None)
        return jsonify({'message': 'Your application has been submitted successfully. We will be in touch!'})
    except Exception as e:
        logger.error(f"Job application submission failed: {e}")
        db.session.rollback()
        return jsonify({'error': 'An unexpected error occurred while submitting your application.'}), 500

# Chatbot API remains the same
@app.route('/api/chatbot', methods=['POST'])
def chatbot_response():
    # ... (code is unchanged)
    if not chatbot:
        return jsonify({'response': 'Sorry, the AI Assistant is currently offline.'})
    user_message = request.json.get('message')
    if not user_message:
        return jsonify({'response': 'I need a message to respond to!'})
    response = chatbot.chat(user_message)
    return jsonify(response)
    
# OTP routes remain the same
@app.route('/api/send-otp', methods=['POST'])
def send_otp():
    # ... (code is unchanged)
    data = request.get_json()
    email = data.get('email')
    if not email: return jsonify({'error': 'Email is required.'}), 400
    if not app.config.get('MAIL_USERNAME'): return jsonify({'error': 'The mail server is not configured.'}), 500
    otp = str(random.randint(100000, 999999))
    session['otp'] = otp
    session['otp_email'] = email
    session['otp_expiry'] = (datetime.utcnow() + timedelta(minutes=10)).isoformat()
    try:
        msg = Message('Your Vendhan Info Tech Verification Code', recipients=[email])
        msg.body = f'Your verification code is: {otp}\nThis code will expire in 10 minutes.'
        mail.send(msg)
        return jsonify({'message': 'Verification code sent to your email.'})
    except Exception as e:
        logger.error(f"Failed to send OTP email to {email}: {e}")
        return jsonify({'error': 'Could not send verification email.'}), 500

@app.route('/api/verify-otp', methods=['POST'])
def verify_otp():
    # ... (code is unchanged)
    data = request.get_json()
    otp_from_user, email_from_user = data.get('otp'), data.get('email')
    otp_in_session, email_in_session, expiry_str = session.get('otp'), session.get('otp_email'), session.get('otp_expiry')
    if not all([otp_from_user, email_from_user, otp_in_session, email_in_session, expiry_str]): return jsonify({'error': 'Invalid request.'}), 400
    if email_from_user != email_in_session: return jsonify({'error': 'Email does not match.'}), 400
    if datetime.utcnow() > datetime.fromisoformat(expiry_str): return jsonify({'error': 'Code has expired.'}), 400
    if otp_from_user == otp_in_session:
        session['otp_verified_email'] = email_in_session
        session.pop('otp', None); session.pop('otp_email', None); session.pop('otp_expiry', None)
        return jsonify({'message': 'Email verified successfully!'})
    else:
        return jsonify({'error': 'Invalid verification code.'}), 400

# ==============================================================================
#  ADMIN PANEL API ROUTES (NEW)
# ==============================================================================
@app.route('/api/dashboard-data', methods=['GET'])
@login_required
def get_dashboard_data():
    stats = {
        'totalApplications': db.session.query(Application).count(),
        'totalMessages': db.session.query(ContactMessage).count(),
        'totalUsers': db.session.query(AdminUser).count(),
        'totalProjects': 0, # Placeholder
        'totalAnnouncements': 0 # Placeholder
    }
    return jsonify({'stats': stats})

@app.route('/api/applications', methods=['GET'])
@login_required
def get_applications():
    apps = Application.query.order_by(Application.submission_date.desc()).all()
    apps_list = [{
        'id': app.id,
        'name': f"{app.first_name} {app.last_name}",
        'position': app.position,
        'date': app.submission_date.strftime('%Y-%m-%d %H:%M'),
        'status': app.status
    } for app in apps]
    return jsonify(apps_list)

@app.route('/api/application/<int:app_id>', methods=['GET'])
@login_required
def get_application_details(app_id):
    app_obj = Application.query.get_or_404(app_id)
    app_dir = os.path.join(app.config['UPLOAD_FOLDER'], app_obj.upload_folder)
    files = []
    if os.path.exists(app_dir):
        files = [f for f in os.listdir(app_dir) if os.path.isfile(os.path.join(app_dir, f))]
    
    replies = [{
        'content': reply.reply_content,
        'date': reply.reply_date.strftime('%Y-%m-%d %H:%M'),
        'author': AdminUser.query.get(reply.author_id).username
    } for reply in app_obj.replies]

    details = {
        'id': app_obj.id,
        'fullName': f"{app_obj.first_name} {app_obj.last_name}",
        'email': app_obj.email,
        'phone': app_obj.phone_number,
        'location': f"{app_obj.city}, {app_obj.district}",
        'position': app_obj.position,
        'date': app_obj.submission_date.strftime('%Y-%m-%d'),
        'status': app_obj.status,
        'files': files,
        'folder': app_obj.upload_folder,
        'replies': replies
    }
    return jsonify(details)

@app.route('/api/application/update-status', methods=['POST'])
@login_required
def update_application_status():
    data = request.get_json()
    app_id = data.get('id')
    new_status = data.get('status')
    app_obj = Application.query.get_or_404(app_id)
    app_obj.status = new_status
    db.session.commit()
    return jsonify({'message': f'Status updated to {new_status}'})

@app.route('/api/messages', methods=['GET'])
@login_required
def get_messages():
    msgs = ContactMessage.query.order_by(ContactMessage.submission_date.desc()).all()
    msgs_list = [{
        'id': msg.id,
        'from': f"{msg.first_name} {msg.last_name}",
        'email': msg.email,
        'subject': msg.message_content[:50] + '...',
        'date': msg.submission_date.strftime('%Y-%m-%d %H:%M'),
        'status': msg.status
    } for msg in msgs]
    return jsonify(msgs_list)

@app.route('/api/message/<int:msg_id>', methods=['GET'])
@login_required
def get_message_details(msg_id):
    msg_obj = ContactMessage.query.get_or_404(msg_id)
    replies = [{
        'content': reply.reply_content,
        'date': reply.reply_date.strftime('%Y-%m-%d %H:%M'),
        'author': AdminUser.query.get(reply.author_id).username
    } for reply in msg_obj.replies]

    details = {
        'id': msg_obj.id,
        'fullName': f"{msg_obj.first_name} {msg_obj.last_name}",
        'email': msg_obj.email,
        'date': msg_obj.submission_date.strftime('%Y-%m-%d'),
        'status': msg_obj.status,
        'message': msg_obj.message_content,
        'replies': replies
    }
    return jsonify(details)

@app.route('/api/reply', methods=['POST'])
@login_required
def handle_reply():
    data = request.get_json()
    item_type = data.get('type')
    item_id = data.get('id')
    content = data.get('content')
    
    if not all([item_type, item_id, content]):
        return jsonify({'error': 'Missing data for reply.'}), 400

    recipient_email = None
    subject = ""
    
    try:
        if item_type == 'application':
            item = Application.query.get_or_404(item_id)
            item.status = 'Replied'
            subject = f"Update on your application for {item.position} at Vendhan Info Tech"
            new_reply = AdminReply(reply_content=content, application=item, author_id=current_user.id)
        elif item_type == 'message':
            item = ContactMessage.query.get_or_404(item_id)
            item.status = 'Replied'
            subject = f"Re: Your inquiry to Vendhan Info Tech"
            new_reply = AdminReply(reply_content=content, message=item, author_id=current_user.id)
        else:
            return jsonify({'error': 'Invalid item type.'}), 400

        recipient_email = item.email
        db.session.add(new_reply)
        db.session.commit()

        # Send the email
        msg = Message(subject, recipients=[recipient_email])
        msg.body = content
        mail.send(msg)
        
        return jsonify({'message': 'Reply sent successfully!'})

    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to send reply: {e}")
        return jsonify({'error': 'Could not send reply email.'}), 500

@app.route('/download/<path:folder>/<path:filename>')
@login_required
def download_file(folder, filename):
    directory = os.path.join(app.config['UPLOAD_FOLDER'], folder)
    return send_from_directory(directory, filename, as_attachment=True)


@app.route('/api/item/delete/<item_type>/<int:item_id>', methods=['POST'])
@login_required
def delete_item(item_type, item_id):
    try:
        if item_type == 'application':
            item = Application.query.get_or_404(item_id)
            folder_path = os.path.join(app.config['UPLOAD_FOLDER'], item.upload_folder)
            if os.path.exists(folder_path):
                shutil.rmtree(folder_path) # Deletes the folder and all its contents
        elif item_type == 'message':
            item = ContactMessage.query.get_or_404(item_id)
        else:
            return jsonify({'error': 'Invalid item type'}), 400
        
        db.session.delete(item)
        db.session.commit()
        return jsonify({'message': f'{item_type.capitalize()} deleted successfully.'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting {item_type} {item_id}: {e}")
        return jsonify({'error': 'An error occurred during deletion.'}), 500


# ==============================================================================
#  RUN THE APP
# ==============================================================================
if __name__ == '__main__':
    with app.app_context():
        # db.create_all() # Use Flask-Migrate instead
        initialize_chatbot()
    app.run(host='0.0.0.0', port=5003, debug=True)