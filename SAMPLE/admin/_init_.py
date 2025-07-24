from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from app import db, User  # Import from the main app.py

admin_bp = Blueprint('admin', __name__, template_folder='templates')
bcrypt = Bcrypt()

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin.index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user, remember=True)
            next_page = request.args.get('next')
            flash('Login successful!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('admin.index'))
        else:
            flash('Login unsuccessful. Please check email and password.', 'danger')
            
    return render_template('admin/login.html', title='Admin Login')


@admin_bp.route('/')
@login_required
def index():
    # Redirect to the main admin view provided by Flask-Admin
    return redirect(url_for('user.index_view'))


@admin_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('admin.login'))