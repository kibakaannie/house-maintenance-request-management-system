from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Tenant, Landlord, PropertyManager, Technician
from functools import wraps

auth_bp = Blueprint('auth', __name__)

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Role required decorator
def role_required(allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_role' not in session or session['user_role'] not in allowed_roles:
                flash('You do not have permission to access this page', 'danger')
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['user_role'] = user.role
            session['user_name'] = user.full_name
            
            flash(f'Welcome back, {user.full_name}!', 'success')
            
            # Redirect based on role
            if user.role == 'tenant':
                return redirect(url_for('tenant_dashboard'))
            elif user.role == 'landlord' or user.role == 'property_manager':
                return redirect(url_for('admin_dashboard'))
            elif user.role == 'technician':
                return redirect(url_for('technician_dashboard'))
        else:
            flash('Invalid email or password', 'danger')
    
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        role = request.form.get('role', 'tenant')
        
        # Check if user exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered', 'danger')
            return redirect(url_for('register'))
        
        # Create user
        hashed_password = generate_password_hash(password)
        user = User(
            full_name=full_name,
            email=email,
            phone=phone,
            password=hashed_password,
            role=role
        )
        db.session.add(user)
        db.session.commit()
        
        # Create role-specific profile
        if role == 'tenant':
            tenant = Tenant(
                user_id=user.id,
                unit_number=request.form.get('unit_number'),
                monthly_rent=float(request.form.get('monthly_rent', 0)),
                balance=0
            )
            db.session.add(tenant)
        elif role == 'technician':
            technician = Technician(
                user_id=user.id,
                specialty=request.form.get('specialty'),
                status='available'
            )
            db.session.add(technician)
        elif role == 'property_manager':
            manager = PropertyManager(
                user_id=user.id,
                department=request.form.get('department', 'Operations')
            )
            db.session.add(manager)
        elif role == 'landlord':
            landlord = Landlord(
                user_id=user.id,
                company_name=request.form.get('company_name')
            )
            db.session.add(landlord)
        
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

@auth_bp.route('/profile')
@login_required
def profile():
    user = User.query.get(session['user_id'])
    return render_template('profile.html', user=user)