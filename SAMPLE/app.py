import os
import random
import logging
from datetime import datetime, timedelta

from flask import Flask, render_template, request, jsonify, url_for, session
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from flask_mail import Mail, Message

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
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 # 16 MB max upload size

# --- Configure Flask-Mail ---
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'true').lower() in ['true', '1', 't']
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')
app.config['MAIL_RECIPIENT'] = os.getenv('MAIL_RECIPIENT')

mail = Mail(app)

# --- Set up logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Initialize Chatbot ---
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

# --- Helper function to check allowed file types ---
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'pdf', 'doc', 'docx'}

# ==============================================================================
#  FRONTEND ROUTES
# ==============================================================================
@app.route('/')
def home(): return render_template('index.html', current_page='home')
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
#  API ROUTES
# ==============================================================================

@app.route('/api/send-otp', methods=['POST'])
def send_otp():
    data = request.get_json()
    email = data.get('email')

    if not email:
        return jsonify({'error': 'Email is required.'}), 400
    if not app.config.get('MAIL_USERNAME'):
        logger.warning("Mail not configured. OTP cannot be sent.")
        return jsonify({'error': 'The mail server is not configured by the administrator.'}), 500

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
        return jsonify({'error': 'Could not send verification email. Please check the address and try again.'}), 500

@app.route('/api/verify-otp', methods=['POST'])
def verify_otp():
    data = request.get_json()
    otp_from_user = data.get('otp')
    email_from_user = data.get('email')

    otp_in_session = session.get('otp')
    email_in_session = session.get('otp_email')
    expiry_str = session.get('otp_expiry')

    if not all([otp_from_user, email_from_user, otp_in_session, email_in_session, expiry_str]):
        return jsonify({'error': 'Invalid request. Please start over.'}), 400
    if email_from_user != email_in_session:
        return jsonify({'error': 'Email does not match the one used for verification.'}), 400
    if datetime.utcnow() > datetime.fromisoformat(expiry_str):
        return jsonify({'error': 'Verification code has expired.'}), 400
    if otp_from_user == otp_in_session:
        session['otp_verified_email'] = email_in_session
        session.pop('otp', None); session.pop('otp_email', None); session.pop('otp_expiry', None)
        return jsonify({'message': 'Email verified successfully!'})
    else:
        return jsonify({'error': 'Invalid verification code.'}), 400

@app.route('/api/contact', methods=['POST'])
def handle_contact():
    form = request.form
    email = form.get('email')
    if session.get('otp_verified_email') != email:
        return jsonify({'error': 'Email not verified. Please complete the verification step.'}), 403
    try:
        msg = Message(
            f"New Contact Form Submission from {form.get('firstName')} {form.get('lastName')}",
            recipients=[app.config['MAIL_RECIPIENT']]
        )
        msg.html = render_template('email/contact_notification.html', data=form)
        mail.send(msg)
        session.pop('otp_verified_email', None)
        return jsonify({'message': 'Thank you! Your message has been sent successfully.'})
    except Exception as e:
        logger.error(f"Contact form email failed to send: {e}")
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
        msg = Message(f"New Job Application: {form.get('position')} - {applicant_name}", recipients=[app.config['MAIL_RECIPIENT']])
        msg.html = render_template('email/application_notification.html', data=form)
        for attachment in attachments:
            with app.open_resource(attachment['path']) as fp:
                msg.attach(attachment['filename'], attachment['content_type'], fp.read())
        mail.send(msg)
        session.pop('otp_verified_email', None)
        return jsonify({'message': 'Your application has been submitted successfully. We will be in touch!'})
    except Exception as e:
        logger.error(f"Job application email failed to send: {e}")
        return jsonify({'error': 'An unexpected error occurred while submitting your application.'}), 500

@app.route('/api/chatbot', methods=['POST'])
def chatbot_response():
    if not chatbot:
        return jsonify({'response': 'Sorry, the AI Assistant is currently offline.'})
    user_message = request.json.get('message')
    if not user_message:
        return jsonify({'response': 'I need a message to respond to!'})
    response = chatbot.chat(user_message)
    return jsonify(response)

# ==============================================================================
#  RUN THE APP
# ==============================================================================
if __name__ == '__main__':
    initialize_chatbot()
    app.run(host='0.0.0.0', port=5003, debug=True)