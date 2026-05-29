from flask import Flask, render_template, request, redirect, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename  # <-- ADD THIS LINE
from datetime import datetime
import json
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-this'

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# File paths for persistent storage
USERS_FILE = 'users.json'
REQUESTS_FILE = 'requests.json'
TECHNICIANS_FILE = 'technicians.json'
PAYMENTS_FILE = 'payments.json'

# ============ LOAD FUNCTIONS ============
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

def load_requests():
    if os.path.exists(REQUESTS_FILE):
        with open(REQUESTS_FILE, 'r') as f:
            data = json.load(f)
            return {int(k): v for k, v in data.items()}
    return {}

def save_requests(requests):
    with open(REQUESTS_FILE, 'w') as f:
        json.dump(requests, f, indent=2)

def load_technicians():
    if os.path.exists(TECHNICIANS_FILE):
        with open(TECHNICIANS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_technicians(technicians):
    with open(TECHNICIANS_FILE, 'w') as f:
        json.dump(technicians, f, indent=2)

def load_payments():
    if os.path.exists(PAYMENTS_FILE):
        with open(PAYMENTS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_payments(payments):
    with open(PAYMENTS_FILE, 'w') as f:
        json.dump(payments, f, indent=2)

# ============ MESSAGING DATA STRUCTURE ============
MESSAGES_FILE = 'messages.json'

def load_messages():
    if os.path.exists(MESSAGES_FILE):
        with open(MESSAGES_FILE, 'r') as f:
            return json.load(f)
    return []

def save_messages(messages):
    with open(MESSAGES_FILE, 'w') as f:
        json.dump(messages, f, indent=2)

# Load messages
messages = load_messages()        

# ============ LOAD EXISTING DATA ============
users = load_users()
maintenance_requests = load_requests()
technicians_list = load_technicians()
payment_history = load_payments()

# Initialize sample payment data if empty
if not payment_history:
    print("📊 Creating sample payment records...")
    sample_payments = [
        {'id': 1, 'tenant_name': 'Alex Johnson', 'property_name': 'Sunset Apartments', 'amount': 18500, 'date': '2024-04-01', 'method': 'M-PESA', 'status': 'completed', 'recorded_by': 'System', 'recorded_at': '2024-04-01 10:00:00'},
        {'id': 2, 'tenant_name': 'Mary Wanjiku', 'property_name': 'Sunset Apartments', 'amount': 17000, 'date': '2024-04-02', 'method': 'Bank Transfer', 'status': 'completed', 'recorded_by': 'System', 'recorded_at': '2024-04-02 10:00:00'},
        {'id': 3, 'tenant_name': 'James Otieno', 'property_name': 'Green Valley Estate', 'amount': 22000, 'date': '2024-04-03', 'method': 'M-PESA', 'status': 'completed', 'recorded_by': 'System', 'recorded_at': '2024-04-03 10:00:00'},
        {'id': 4, 'tenant_name': 'Alex Johnson', 'property_name': 'Sunset Apartments', 'amount': 18500, 'date': '2024-03-01', 'method': 'M-PESA', 'status': 'completed', 'recorded_by': 'System', 'recorded_at': '2024-03-01 10:00:00'},
        {'id': 5, 'tenant_name': 'Mary Wanjiku', 'property_name': 'Sunset Apartments', 'amount': 17000, 'date': '2024-03-02', 'method': 'Bank Transfer', 'status': 'completed', 'recorded_by': 'System', 'recorded_at': '2024-03-02 10:00:00'},
        {'id': 6, 'tenant_name': 'James Otieno', 'property_name': 'Green Valley Estate', 'amount': 22000, 'date': '2024-03-03', 'method': 'M-PESA', 'status': 'completed', 'recorded_by': 'System', 'recorded_at': '2024-03-03 10:00:00'},
    ]
    payment_history.extend(sample_payments)
    save_payments(payment_history)
    print(f"✓ Created {len(sample_payments)} sample payment records")
else:
    print(f"✓ Loaded {len(payment_history)} existing payment records")

technician_assignments = {}
request_counter = max(maintenance_requests.keys()) + 1 if maintenance_requests else 1

# ============ TEMPLATE FILTER ============
@app.template_filter('format_currency')
def format_currency(value):
    if value is None:
        value = 0
    return f"{value:,.2f}"

# ============ MAIN ROUTES ============
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if email in users and check_password_hash(users[email]['password'], password):
            session['user_id'] = email
            session['user_name'] = users[email]['name']
            session['user_role'] = users[email]['role']
            flash(f'Welcome back, {users[email]["name"]}!', 'success')
            
            if users[email]['role'] == 'tenant':
                return redirect('/tenant/dashboard')
            elif users[email]['role'] in ['landlord', 'property_manager']:
                return redirect('/admin/dashboard')
            elif users[email]['role'] == 'technician':
                return redirect('/technician/dashboard')
        else:
            flash('Invalid credentials', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        role = request.form.get('role')
        
        if not full_name or not email or not password: 
            flash('All fields are required', 'danger')
            return redirect('/register')
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return redirect('/register')
        
        if email in users:
            flash('Email already registered', 'danger')
            return redirect('/login')
        
        users[email] = {
            'name': full_name,
            'email': email,
            'password': generate_password_hash(password),
            'role': role,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        save_users(users)
        
        if role == 'technician':
            technicians_list.append({'email': email, 'name': full_name})
            save_technicians(technicians_list)
        
        flash('Registration successful! Please login.', 'success')
        return redirect('/login')
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect('/')

# ============ TENANT ROUTES ============
@app.route('/tenant/dashboard')
def tenant_dashboard():
    print(f"=== DEBUG ===")
    print(f"Session user_id: {session.get('user_id')}")
    print(f"Session user_role: {session.get('user_role')}")
    print(f"Session user_name: {session.get('user_name')}")
    
    if 'user_id' not in session:
        flash('Please login first', 'warning')
        return redirect('/login')
    
    if session.get('user_role') != 'tenant':
        flash('Access denied', 'danger')
        return redirect('/')
    
    return render_template('tenant_dashboard.html', user_name=session.get('user_name'))

@app.route('/tenant/maintenance')
def tenant_maintenance():
    if 'user_id' not in session:
        flash('Please login first', 'warning')
        return redirect('/login')
    
    if session.get('user_role') != 'tenant':
        flash('Access denied', 'danger')
        return redirect('/')
    
    return render_template('tenant_maintenance.html', user_name=session.get('user_name'))

@app.route('/tenant/new-request', methods=['GET', 'POST'])
def tenant_new_request():
    global request_counter
    
    if 'user_id' not in session:
        flash('Please login first', 'warning')
        return redirect('/login')
    
    if request.method == 'POST':
        title = request.form.get('title')
        priority = request.form.get('priority')
        description = request.form.get('description')
        
        if not title or not description:
            flash('Please fill in all required fields', 'danger')
            return redirect('/tenant/new-request')
        
        new_request = {
            'id': request_counter,
            'title': title,
            'description': description,
            'priority': priority,
            'status': 'pending',
            'date': datetime.now().strftime('%Y-%m-%d'),
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'tenant_email': session['user_id'],
            'tenant_name': session['user_name'],
            'technician_email': None,
            'technician_name': 'Not assigned yet',
            'estimated_cost': None,
            'image_url': None
        }
        
        maintenance_requests[request_counter] = new_request
        save_requests(maintenance_requests)
        request_counter += 1
        
        flash(f'Maintenance request "{title}" submitted successfully!', 'success')
        return redirect('/tenant/maintenance')
    
    return render_template('tenant_new_request.html', user_name=session.get('user_name'))

@app.route('/tenant/messages')
def tenant_messages():
    if 'user_id' not in session:
        flash('Please login first', 'warning')
        return redirect('/login')
    
    if session.get('user_role') != 'tenant':
        flash('Access denied', 'danger')
        return redirect('/')
    
    # Get messages for this tenant
    user_email = session['user_id']
    user_messages = [m for m in messages if m['recipient_email'] == user_email or m['sender_email'] == user_email]
    user_messages.sort(key=lambda x: x['created_at'], reverse=True)
    
    return render_template('messages.html', 
                         user_name=session.get('user_name'),
                         user_role='tenant',
                         messages=user_messages,
                         users=users)

@app.route('/tenant/rent')
def tenant_rent():
    if 'user_id' not in session:
        flash('Please login first', 'warning')
        return redirect('/login')
    
    if session.get('user_role') != 'tenant':
        flash('Access denied', 'danger')
        return redirect('/')
    
    return render_template('tenant_rent.html', user_name=session.get('user_name'))
# ============ TENANTS ROUTE ============
@app.route('/admin/tenants')
def admin_tenants():
    if 'user_id' not in session:
        flash('Please login first', 'warning')
        return redirect('/login')
    
    if session.get('user_role') not in ['landlord', 'property_manager']:
        flash('Access denied', 'danger')
        return redirect('/')
    
    # Get all tenants from users
    tenants_list = []
    for email, user_data in users.items():
        if user_data.get('role') == 'tenant':
            tenant_info = {
                'name': user_data.get('name', 'Unknown'),
                'email': email,
                'phone': user_data.get('phone', 'N/A'),
                'unit_number': 'Apt 4B',
                'floor': '4th Floor',
                'property_name': 'Sunset Apartments',
                'monthly_rent': 18500,
                'balance': 0
            }
            tenants_list.append(tenant_info)
    
    return render_template('admin_tenants.html', 
                         user_name=session.get('user_name'),
                         tenants=tenants_list)

# ============ MESSAGING ROUTES ============
@app.route('/messages')
def view_messages():
    if 'user_id' not in session:
        flash('Please login first', 'warning')
        return redirect('/login')
    
    user_email = session['user_id']
    user_role = session['user_role']
    
    # Get messages for this user
    if user_role == 'tenant':
        user_messages = [m for m in messages if m['recipient_email'] == user_email or m['sender_email'] == user_email]
    else:
        # Admin/Manager sees all messages
        user_messages = messages
    
    # Sort by date (newest first)
    user_messages.sort(key=lambda x: x['created_at'], reverse=True)
    
    # Pass users to the template
    return render_template('messages.html', 
                         user_name=session.get('user_name'),
                         user_role=user_role,
                         messages=user_messages,
                         users=users)  # <-- ADD THIS LINE

@app.route('/send-message', methods=['POST'])
def send_message():
    if 'user_id' not in session:
        flash('Please login first', 'warning')
        return redirect('/login')
    
    recipient_email = request.form.get('recipient_email')
    subject = request.form.get('subject')
    message_text = request.form.get('message')
    
    if not recipient_email or not subject or not message_text:
        flash('All fields are required', 'danger')
        return redirect('/messages')
    
    # For tenants, automatically send to property manager
    if session['user_role'] == 'tenant':
        # Find property manager email (first admin user)
        property_manager_email = None
        for email, user_data in users.items():
            if user_data['role'] in ['property_manager', 'landlord']:
                property_manager_email = email
                recipient_name = user_data['name']
                break
        
        if property_manager_email:
            recipient_email = property_manager_email
        else:
            # For demo purposes, send to first admin if no property manager exists
            for email, user_data in users.items():
                if user_data['role'] != 'tenant':
                    recipient_email = email
                    recipient_name = user_data['name']
                    break
    
    # Get recipient name
    recipient_name = users.get(recipient_email, {}).get('name', recipient_email)
    
    new_message = {
        'id': len(messages) + 1,
        'sender_email': session['user_id'],
        'sender_name': session['user_name'],
        'sender_role': session['user_role'],
        'recipient_email': recipient_email,
        'recipient_name': recipient_name,
        'subject': subject,
        'message': message_text,
        'is_read': False,
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    messages.append(new_message)
    save_messages(messages)
    
    flash('Message sent successfully!', 'success')
    return redirect('/messages')

@app.route('/message/<int:message_id>')
def view_message(message_id):
    if 'user_id' not in session:
        flash('Please login first', 'warning')
        return redirect('/login')
    
    # Find the message
    message = None
    for m in messages:
        if m['id'] == message_id:
            message = m
            break
    
    if not message:
        flash('Message not found', 'danger')
        return redirect('/messages')
    
    # Mark as read if user is recipient
    if message['recipient_email'] == session['user_id'] and not message['is_read']:
        message['is_read'] = True
        save_messages(messages)
    
    return render_template('view_message.html', 
                         user_name=session.get('user_name'),
                         message=message)

@app.route('/reply-message/<int:message_id>', methods=['POST'])
def reply_message(message_id):
    if 'user_id' not in session:
        flash('Please login first', 'warning')
        return redirect('/login')
    
    # Find original message
    original = None
    for m in messages:
        if m['id'] == message_id:
            original = m
            break
    
    if not original:
        flash('Message not found', 'danger')
        return redirect('/messages')
    
    reply_text = request.form.get('reply')
    
    if not reply_text:
        flash('Reply cannot be empty', 'danger')
        return redirect(f'/message/{message_id}')
    
    # Determine recipient (original sender)
    if original['sender_email'] == session['user_id']:
        recipient_email = original['recipient_email']
        recipient_name = original['recipient_name']
    else:
        recipient_email = original['sender_email']
        recipient_name = original['sender_name']
    
    new_message = {
        'id': len(messages) + 1,
        'sender_email': session['user_id'],
        'sender_name': session['user_name'],
        'sender_role': session['user_role'],
        'recipient_email': recipient_email,
        'recipient_name': recipient_name,
        'subject': f"Re: {original['subject']}",
        'message': reply_text,
        'is_read': False,
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'in_reply_to': message_id
    }
    

    messages.append(new_message)
    save_messages(messages)
    
    flash('Reply sent successfully!', 'success')
    return redirect('/messages')

# ============ ADMIN ROUTES ============
@app.route('/admin/dashboard')
def admin_dashboard():
    if 'user_id' not in session:
        flash('Please login first', 'warning')
        return redirect('/login')
    
    if session.get('user_role') not in ['landlord', 'property_manager']:
        flash('Access denied', 'danger')
        return redirect('/')
    
    # Count tenants
    tenants_count = len([u for u in users.values() if u.get('role') == 'tenant'])
    
    # You can add these counts from your data
    properties_count = 2  # Update with actual count
    vacancies_count = 2   # Update with actual count
    pending_maintenance = len([r for r in maintenance_requests.values() if r.get('status') == 'pending'])
    
    return render_template('admin_dashboard.html', 
                         user_name=session.get('user_name'),
                         tenants_count=tenants_count,
                         properties_count=properties_count,
                         vacancies_count=vacancies_count,
                         pending_maintenance=pending_maintenance)

@app.route('/admin/assign-request/<int:request_id>', methods=['POST'])
def admin_assign_request(request_id):
    if 'user_id' not in session:
        flash('Please login first', 'warning')
        return redirect('/login')
    
    technician_email = request.form.get('technician_email')
    
    if request_id in maintenance_requests:
        maintenance_requests[request_id]['technician_email'] = technician_email
        maintenance_requests[request_id]['status'] = 'in_progress'
        
        for tech in technicians_list:
            if tech['email'] == technician_email:
                maintenance_requests[request_id]['technician_name'] = tech['name']
                break
        
        save_requests(maintenance_requests)
        flash(f'Request #{request_id} assigned to technician', 'success')
    
    return redirect('/admin/maintenance')

# Properties Route
@app.route('/admin/properties')
def admin_properties():
    if 'user_id' not in session:
        flash('Please login first', 'warning')
        return redirect('/login')
    
    if session.get('user_role') not in ['landlord', 'property_manager']:
        flash('Access denied', 'danger')
        return redirect('/')
    
    # Create sample data
    properties = [
        {
            'name': 'Sunset Apartments',
            'address': '123 Main Street, Nairobi',
            'total_units': 20,
            'occupied': 18,
            'vacant': 2,
            'occupancy_rate': 90,
            'created_at': '2024-01-15'
        },
        {
            'name': 'Green Valley Estate',
            'address': '45 Park Road, Kiambu',
            'total_units': 15,
            'occupied': 14,
            'vacant': 1,
            'occupancy_rate': 93,
            'created_at': '2024-02-20'
        }
    ]
    
    total_units = 35
    total_tenants = 32
    
    # Debug print to confirm data is being sent
    print(f"Properties being sent: {len(properties)}")
    print(f"Total units: {total_units}")
    
    return render_template('admin_properties.html', 
                         user_name=session.get('user_name'),
                         properties=properties,
                         total_units=total_units,
                         total_tenants=total_tenants)

# Vacancies Route
@app.route('/admin/vacancies')
def admin_vacancies():
    if 'user_id' not in session:
        flash('Please login first', 'warning')
        return redirect('/login')
    
    if session.get('user_role') not in ['landlord', 'property_manager']:
        flash('Access denied', 'danger')
        return redirect('/')
    
    # Sample vacancy data - replace with your database
    vacancies = [
        {'unit_number': 'Apt 2A', 'property_name': 'Sunset Apartments', 'bedrooms': 2, 'bathrooms': 1, 'floor': '2nd', 'monthly_rent': 17000, 'status': 'vacant'},
        {'unit_number': 'Studio 1C', 'property_name': 'Sunset Apartments', 'bedrooms': 0, 'bathrooms': 1, 'floor': '1st', 'monthly_rent': 14000, 'status': 'vacant'},
        {'unit_number': 'Unit 5B', 'property_name': 'Green Valley Estate', 'bedrooms': 1, 'bathrooms': 1, 'floor': '5th', 'monthly_rent': 22000, 'status': 'vacant'},
        {'unit_number': 'Apt 3D', 'property_name': 'Sunset Apartments', 'bedrooms': 3, 'bathrooms': 2, 'floor': '3rd', 'monthly_rent': 25000, 'status': 'vacant'},
    ]
    
    # Count vacancies by type
    bedsitter_count = len([v for v in vacancies if v['bedrooms'] == 0])
    one_bedroom_count = len([v for v in vacancies if v['bedrooms'] == 1])
    two_bedroom_count = len([v for v in vacancies if v['bedrooms'] == 2])
    three_bedroom_count = len([v for v in vacancies if v['bedrooms'] >= 3])
    
    return render_template('admin_vacancies.html', 
                         user_name=session.get('user_name'),
                         vacancies=vacancies,
                         bedsitter_count=bedsitter_count,
                         one_bedroom_count=one_bedroom_count,
                         two_bedroom_count=two_bedroom_count,
                         three_bedroom_count=three_bedroom_count,
                         total_vacancies=len(vacancies))

# Maintenance Route (update your existing one)
@app.route('/admin/maintenance')
def admin_maintenance():
    if 'user_id' not in session:
        flash('Please login first', 'warning')
        return redirect('/login')
    
    if session.get('user_role') not in ['landlord', 'property_manager']:
        flash('Access denied', 'danger')
        return redirect('/')
    
    # Get all maintenance requests
    all_requests = list(maintenance_requests.values())
    
    # Calculate counts
    pending_count = len([r for r in all_requests if r.get('status') == 'pending'])
    in_progress_count = len([r for r in all_requests if r.get('status') == 'in_progress'])
    completed_count = len([r for r in all_requests if r.get('status') == 'completed'])
    
    return render_template('admin_maintenance.html', 
                         user_name=session.get('user_name'),
                         maintenance_requests=all_requests,
                         pending_count=pending_count,
                         in_progress_count=in_progress_count,
                         completed_count=completed_count)

# ============ FINANCE ROUTES (ONLY ONCE!) ============
@app.route('/admin/finance')
def admin_finance():
    if 'user_id' not in session:
        flash('Please login first', 'warning')
        return redirect('/login')
    
    if session.get('user_role') not in ['landlord', 'property_manager']:
        flash('Access denied', 'danger')
        return redirect('/')
    
    # Calculate total income
    total_income = sum([p['amount'] for p in payment_history if p['status'] == 'completed'])
    
    # Calculate monthly income (last 6 months)
    monthly_data = {}
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    for i in range(6):
        month_num = current_month - i
        year = current_year
        if month_num <= 0:
            month_num += 12
            year -= 1
        
        month_name = datetime(year, month_num, 1).strftime('%B')
        monthly_data[month_name] = 0
    
    for payment in payment_history:
        if payment['status'] == 'completed':
            payment_date = datetime.strptime(payment['date'], '%Y-%m-%d')
            month_name = payment_date.strftime('%B')
            if month_name in monthly_data:
                monthly_data[month_name] += payment['amount']
    
    # Calculate income by property
    income_by_property = {}
    for payment in payment_history:
        if payment['status'] == 'completed':
            prop_name = payment.get('property_name', 'Sunset Apartments')
            income_by_property[prop_name] = income_by_property.get(prop_name, 0) + payment['amount']
    
    # Get recent payments
    recent_payments = sorted(payment_history, key=lambda x: x['date'], reverse=True)[:10]
    
    return render_template('admin_finance.html',
                         user_name=session.get('user_name'),
                         total_income=total_income,
                         monthly_data=monthly_data,
                         income_by_property=income_by_property,
                         recent_payments=recent_payments,
                         total_payments=len(payment_history))

@app.route('/admin/add-payment', methods=['POST'])
def add_payment():
    if 'user_id' not in session:
        flash('Please login first', 'warning')
        return redirect('/login')
    
    tenant_name = request.form.get('tenant_name')
    property_name = request.form.get('property_name')
    amount = float(request.form.get('amount'))
    payment_date = request.form.get('payment_date')
    method = request.form.get('method')
    
    payment = {
        'id': len(payment_history) + 1,
        'tenant_name': tenant_name,
        'property_name': property_name,
        'amount': amount,
        'date': payment_date,
        'method': method,
        'status': 'completed',
        'recorded_by': session.get('user_name'),
        'recorded_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    payment_history.append(payment)
    save_payments(payment_history)
    
    flash(f'Payment of KSh {amount:,.2f} recorded for {tenant_name}', 'success')
    return redirect('/admin/finance')

# ============ TECHNICIAN ROUTES ============
@app.route('/technician/dashboard')
def technician_dashboard():
    if 'user_id' not in session:
        flash('Please login first', 'warning')
        return redirect('/login')
    
    technician_email = session['user_id']
    assigned_requests = [r for r in maintenance_requests.values() if r.get('technician_email') == technician_email]
    pending_count = len([r for r in assigned_requests if r['status'] == 'in_progress'])
    completed_count = len([r for r in assigned_requests if r['status'] == 'completed'])
    
    return render_template('technician_dashboard.html', 
                         user_name=session.get('user_name'),
                         assigned_requests=assigned_requests,
                         pending_count=pending_count,
                         completed_count=completed_count)

@app.route('/technician/requests')
def technician_requests():
    if 'user_id' not in session:
        flash('Please login first', 'warning')
        return redirect('/login')
    
    technician_email = session['user_id']
    assigned_requests = [r for r in maintenance_requests.values() if r.get('technician_email') == technician_email]
    
    return render_template('technician_requests.html', 
                         user_name=session.get('user_name'),
                         assigned_requests=assigned_requests)

@app.route('/technician/update-status/<int:request_id>', methods=['POST'])
def technician_update_status(request_id):
    if 'user_id' not in session:
        flash('Please login first', 'warning')
        return redirect('/login')
    
    new_status = request.form.get('status')
    estimated_cost = request.form.get('estimated_cost')
    
    if request_id in maintenance_requests:
        maintenance_requests[request_id]['status'] = new_status
        if estimated_cost:
            maintenance_requests[request_id]['estimated_cost'] = float(estimated_cost)
        
        save_requests(maintenance_requests)
        flash(f'Request #{request_id} status updated to {new_status}', 'success')
    
    return redirect('/technician/requests')

@app.route('/technician/request/<int:request_id>')
def technician_view_request(request_id):
    if 'user_id' not in session:
        flash('Please login first', 'warning')
        return redirect('/login')
    
    technician_email = session['user_id']
    
    if request_id not in maintenance_requests:
        flash('Request not found', 'danger')
        return redirect('/technician/requests')
    
    request_data = maintenance_requests[request_id]
    
    if request_data.get('technician_email') != technician_email:
        flash('You are not authorized to view this request', 'danger')
        return redirect('/technician/requests')
    
    return render_template('technician_view_request.html', 
                         user_name=session.get('user_name'),
                         request=request_data)

if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("🏠 PROPERTY MANAGEMENT SYSTEM")
    print("=" * 60)
    print("✅ Server starting...")
    print("🌐 Open: http://127.0.0.1:5000")
    print("=" * 60 + "\n")
    app.run(debug=True, host='127.0.0.1', port=5000)