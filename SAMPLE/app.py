import os
import random
import logging
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature
from flask_mail import Mail, Message
from flask_cors import CORS
from download_model import create_enhanced_chatbot

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# --- Configuration ---
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'a-very-secure-and-random-default-key')
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(base_dir, 'site.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(base_dir, 'uploads', 'applications')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'true').lower() in ['true', '1', 't']
app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL', 'false').lower() in ['true', '1', 't']
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', os.getenv('MAIL_USERNAME'))
app.config['MAIL_RECIPIENT'] = os.getenv('MAIL_RECIPIENT')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

db = SQLAlchemy(app)
mail = Mail(app)
serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

# --- Database Models (Unchanged) ---
class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    firstName = db.Column(db.String(100), nullable=False)
    lastName = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class DetailedJobApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    firstName = db.Column(db.String(100), nullable=False)
    lastName = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phoneNumber = db.Column(db.String(20), nullable=False)
    position = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    district = db.Column(db.String(100), nullable=False)
    qualification = db.Column(db.String(100))
    tenth_percentage = db.Column(db.Float)
    twelfth_percentage = db.Column(db.Float)
    ug_university = db.Column(db.String(200))
    ug_percentage = db.Column(db.Float)
    pg_university = db.Column(db.String(200))
    pg_percentage = db.Column(db.Float)
    resume_path = db.Column(db.String(300), nullable=False)
    tenth_cert_path = db.Column(db.String(300))
    twelfth_cert_path = db.Column(db.String(300))
    ug_cert_path = db.Column(db.String(300))
    pg_cert_path = db.Column(db.String(300))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class OTPVerification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False, index=True)
    otp = db.Column(db.String(6), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    verified = db.Column(db.Boolean, default=False)

# --- Chatbot Initialization (Unchanged) ---
chatbot = None
def initialize_chatbot():
    global chatbot
    try:
        logger.info("Initializing chatbot...")
        chatbot = create_enhanced_chatbot()
        chatbot.load_model()
        logger.info("Chatbot initialized successfully!")
    except Exception as e:
        logger.error(f"Failed to initialize chatbot: {e}", exc_info=True)
        chatbot = None

# --- Utility Functions (Unchanged) ---
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png'}

def save_file(file, applicant_name):
    if file and allowed_file(file.filename):
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
        original_filename, extension = os.path.splitext(secure_filename(file.filename))
        unique_filename = f"{applicant_name}_{timestamp}_{original_filename}{extension}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)
        return unique_filename
    return None

# --- Page Rendering Routes ---
@app.route('/')
def home(): 
    return render_template('index.html', current_page='home')

@app.route('/about-us')
def about_details():
    return render_template('about_details.html', current_page='about')

# NEW ROUTE FOR MISSION & VISION PAGE
@app.route('/about-us/mission-vision')
def mission_vision():
    return render_template('mission_vision.html', current_page='about')

@app.route('/services')
def services_overview():
    return render_template('services_overview.html', current_page='services')

@app.route('/services/ai-machine-learning')
def services_ai(): 
    return render_template('ai_service.html', current_page='services')

@app.route('/services/digital-transformation')
def services_digital(): 
    return render_template('digital_services.html', current_page='services')

@app.route('/services/software-development')
def services_software(): 
    return render_template('software_services.html', current_page='services')

@app.route('/services/data-cybersecurity')
def services_cybersecurity(): 
    return render_template('cybersecurity_services.html', current_page='services')

@app.route('/careers')
def careers_overview():
    return render_template('careers_overview.html', current_page='careers')

@app.route('/careers/apply')
def application_form():
    return render_template('application_form.html', current_page='careers')

@app.route('/announcements')
def announcements_page():
    return render_template('announcements_page.html', current_page='announcements')

@app.route('/portfolio/ai-logistics-platform')
def portfolio_logistics():
    return render_template('portfolio_logistics.html', current_page='portfolio')

@app.route('/portfolio/cloud-migration-strategy')
def portfolio_cloud():
    return render_template('portfolio_cloud.html', current_page='portfolio')

@app.route('/portfolio/secure-fintech-application')
def portfolio_fintech():
    return render_template('portfolio_fintech.html', current_page='portfolio')

@app.route('/portfolio/enterprise-erp-implementation')
def portfolio_erp():
    return render_template('portfolio_erp.html', current_page='portfolio')

@app.route('/contact-us')
def contact_page():
    return render_template('contact.html', current_page='contact')


# --- API ROUTES (Unchanged) ---
# ... (all API routes from /api/send-otp to /api/chat remain exactly the same) ...
@app.route('/api/send-otp', methods=['POST'])
def send_otp():
    email = request.json.get('email')
    if not email: return jsonify({'message': 'Email is required.'}), 400
    if not app.config.get('MAIL_USERNAME'):
        logger.error("Mail is not configured. Check your .env file.")
        return jsonify({'message': 'Mail server is not configured. Cannot send email.'}), 503
    OTPVerification.query.filter_by(email=email, verified=False).delete()
    db.session.commit()
    otp_code = f"{random.randint(100000, 999999):06d}"
    expires = datetime.utcnow() + timedelta(minutes=5)
    new_otp = OTPVerification(email=email, otp=otp_code, expires_at=expires)
    try:
        msg = Message("Your Vendhan Info Tech Verification Code", recipients=[email])
        msg.html = f"<p>Your verification code is: <b>{otp_code}</b></p><p>This code is valid for 5 minutes.</p>"
        mail.send(msg)
        db.session.add(new_otp)
        db.session.commit()
        logger.info(f"Successfully sent OTP to {email}")
        return jsonify({'message': 'A 6-digit verification code has been sent to your email.'}), 200
    except Exception as e:
        logger.error(f"Failed to send OTP email to {email}: {e}", exc_info=True)
        db.session.rollback()
        return jsonify({'message': 'Failed to send verification email. Please try again or contact support.'}), 500

@app.route('/api/verify-otp', methods=['POST'])
def verify_otp():
    email = request.json.get('email')
    otp_code = request.json.get('otp')
    form_type = request.json.get('form_type', 'contact')
    if not email or not otp_code: return jsonify({'message': 'Email and OTP are required.'}), 400
    record = OTPVerification.query.filter_by(email=email, otp=otp_code, verified=False).order_by(OTPVerification.created_at.desc()).first()
    if not record: return jsonify({'verified': False, 'message': 'Invalid verification code.'}), 400
    if datetime.utcnow() > record.expires_at: 
        return jsonify({'verified': False, 'message': 'This code has expired. Please request a new one.'}), 400
    record.verified = True
    db.session.commit()
    salt = 'job-application-verification' if form_type == 'job' else 'contact-form-verification'
    token = serializer.dumps(email, salt=salt)
    return jsonify({'verified': True, 'token': token}), 200

@app.route('/api/detailed-apply', methods=['POST'])
def handle_detailed_application():
    try:
        data = request.form
        token, email_from_form = data.get('verification_token'), data.get('email')
        if not token: return jsonify({'message': 'Verification token is missing.'}), 401
        try:
            email_from_token = serializer.loads(token, salt='job-application-verification', max_age=3600)
        except (SignatureExpired, BadTimeSignature):
            return jsonify({'message': 'Your verification is invalid or has expired. Please verify your email again.'}), 401
        if email_from_token != email_from_form:
            return jsonify({'message': 'Email verification mismatch. Please use the same email you verified.'}), 403
        if 'resume' not in request.files: return jsonify({'message': 'Resume file is required.'}), 400
        
        applicant_name = f"{data.get('firstName', 'anon')}_{data.get('lastName', 'user')}"
        resume_file = request.files.get('resume')
        resume_path = save_file(resume_file, f"{applicant_name}_resume")
        if not resume_path: return jsonify({'message': 'Invalid resume file type. Please upload PDF, DOC, or DOCX.'}), 400

        new_app = DetailedJobApplication(
            firstName=data.get('firstName'), lastName=data.get('lastName'), email=data.get('email'),
            phoneNumber=data.get('phoneNumber'), position=data.get('position'), city=data.get('city'), district=data.get('district'),
            qualification=data.get('qualification'), tenth_percentage=data.get('tenth_percentage') or None,
            twelfth_percentage=data.get('twelfth_percentage') or None, ug_university=data.get('ug_university'),
            ug_percentage=data.get('ug_percentage') or None, pg_university=data.get('pg_university'),
            pg_percentage=data.get('pg_percentage') or None, resume_path=resume_path,
            tenth_cert_path=save_file(request.files.get('tenth_cert'), f"{applicant_name}_10th"),
            twelfth_cert_path=save_file(request.files.get('twelfth_cert'), f"{applicant_name}_12th"),
            ug_cert_path=save_file(request.files.get('ug_cert'), f"{applicant_name}_ug"),
            pg_cert_path=save_file(request.files.get('pg_cert'), f"{applicant_name}_pg"),
        )
        db.session.add(new_app)

        admin_recipient = app.config.get('MAIL_RECIPIENT')
        if admin_recipient:
            try:
                msg_subject = f"New Job Application: {data.get('position')} - {data.get('firstName')} {data.get('lastName')}"
                msg_body = f"Details in admin panel for {data.get('email')}"
                admin_msg = Message(subject=msg_subject, recipients=[admin_recipient], body=msg_body)
                mail.send(admin_msg)
            except Exception as e:
                logger.error(f"Failed to send admin notification for job application: {e}", exc_info=True)

        db.session.commit()
        return jsonify({'message': 'Application submitted successfully! We will get back to you shortly.'}), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"ERROR in /api/detailed-apply: {e}", exc_info=True)
        return jsonify({'message': 'An internal server error occurred while processing your application.'}), 500

@app.route('/api/contact', methods=['POST'])
def handle_contact():
    try:
        data = request.form
        token, email_from_form = data.get('verification_token'), data.get('email')
        if not token: return jsonify({'message': 'Verification token is missing.'}), 401
        try:
            email_from_token = serializer.loads(token, salt='contact-form-verification', max_age=3600)
        except (SignatureExpired, BadTimeSignature): return jsonify({'message': 'Verification is invalid or has expired.'}), 401
        if email_from_token != email_from_form: return jsonify({'message': 'Email verification mismatch.'}), 403
        
        new_message = ContactMessage(firstName=data.get('firstName'), lastName=data.get('lastName'), email=data.get('email'), message=data.get('message'))
        db.session.add(new_message)
        
        admin_recipient = app.config.get('MAIL_RECIPIENT')
        if admin_recipient:
            try:
                msg_subject = f"New Contact Message from {data.get('firstName')}"
                msg_body = f"From: {data.get('firstName')} {data.get('lastName')} <{data.get('email')}>\n\nMessage:\n{data.get('message')}"
                admin_msg = Message(subject=msg_subject, recipients=[admin_recipient], body=msg_body)
                mail.send(admin_msg)
            except Exception as e:
                logger.error(f"Failed to send admin notification for contact message: {e}", exc_info=True)
            
        db.session.commit()
        return jsonify({'message': 'Message sent successfully! We will be in touch soon.'}), 200
    except Exception as e:
        db.session.rollback() 
        logger.error(f"ERROR in /api/contact: {e}", exc_info=True) 
        return jsonify({'message': 'An internal server error occurred.'}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    if not chatbot:
        logger.warning("Chatbot not initialized, attempting to reinitialize.")
        initialize_chatbot()
        if not chatbot: return jsonify({'response': 'Sorry, the AI Assistant is currently offline. Please try again later.'}), 503
    try:
        user_message = request.json.get('message', '').strip()
        if not user_message: return jsonify({'error': 'Empty message'}), 400
        return jsonify(chatbot.chat(user_message))
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        return jsonify({'response': "An error occurred on my end. Please try again."}), 500

# --- Main Execution Block ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        initialize_chatbot()
    app.run(debug=True, port=5003)