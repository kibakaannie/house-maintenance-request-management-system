from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import db, User, Tenant, MaintenanceRequest, Communication, RentPayment, Notice
from .auth import login_required, role_required
from datetime import datetime
import os
from werkzeug.utils import secure_filename

tenant_bp = Blueprint('tenant', __name__)

# Configure upload folder
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@tenant_bp.route('/dashboard')
@login_required
@role_required(['tenant'])
def dashboard():
    user = User.query.get(session['user_id'])
    tenant = Tenant.query.filter_by(user_id=user.id).first()
    
    # Get latest rent payment
    latest_rent = RentPayment.query.filter_by(tenant_id=tenant.id).order_by(RentPayment.due_date.desc()).first()
    
    # Get open maintenance requests
    open_requests = MaintenanceRequest.query.filter_by(tenant_id=tenant.id).filter(
        MaintenanceRequest.status != 'completed'
    ).all()
    
    # Get unread messages count for this tenant
    reqs = MaintenanceRequest.query.filter_by(tenant_id=tenant.id).all()
    req_ids = [r.id for r in reqs]
    if req_ids:
        unread_count = Communication.query.filter(Communication.request_id.in_(req_ids), Communication.is_read==False).count()
    else:
        unread_count = 0
    
    # Get notice if any
    notice = Notice.query.filter_by(tenant_id=tenant.id, status='active').first()
    
    return render_template('tenant/tenant_dashboard.html',
                         current_user=user,
                         tenant=tenant,
                         latest_rent=latest_rent,
                         open_requests=open_requests,
                         unread_count=unread_count,
                         notice=notice)

@tenant_bp.route('/maintenance', methods=['GET', 'POST'])
@login_required
@role_required(['tenant'])
def maintenance():
    user = User.query.get(session['user_id'])
    tenant = Tenant.query.filter_by(user_id=user.id).first()
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        unit_number = tenant.unit_number
        
        # Handle image upload
        image_url = None
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                file.save(filepath)
                image_url = f'/static/uploads/{filename}'
        
        maintenance_request = MaintenanceRequest(
            tenant_id=tenant.id,
            title=title,
            description=description,
            unit_number=unit_number,
            image_url=image_url,
            status='pending',
            created_at=datetime.now()
        )
        db.session.add(maintenance_request)
        db.session.commit()
        
        # Add initial communication
        comm = Communication(
            request_id=maintenance_request.id,
            sender_role='tenant',
            sender_name=user.full_name,
            message=f"New maintenance request: {title} - {description}",
            timestamp=datetime.now()
        )
        db.session.add(comm)
        db.session.commit()
        
        flash('Maintenance request submitted successfully', 'success')
        return redirect(url_for('tenant.maintenance'))
    
    # GET request - show all requests
    requests = MaintenanceRequest.query.filter_by(tenant_id=tenant.id).order_by(
        MaintenanceRequest.created_at.desc()
    ).all()
    
    return render_template('tenant/maintenance.html', requests=requests, tenant=tenant)

@tenant_bp.route('/maintenance/<int:id>')
@login_required
@role_required(['tenant'])
def view_maintenance(id):
    user = User.query.get(session['user_id'])
    tenant = Tenant.query.filter_by(user_id=user.id).first()
    request_obj = MaintenanceRequest.query.get_or_404(id)
    
    # Verify ownership
    if request_obj.tenant_id != tenant.id:
        flash('Access denied', 'danger')
        return redirect(url_for('tenant_dashboard'))
    
    communications = Communication.query.filter_by(request_id=id).order_by(Communication.timestamp.asc()).all()
    
    return render_template('tenant/view_maintenance.html', 
                         request=request_obj, 
                         communications=communications)

@tenant_bp.route('/maintenance/<int:id>/message', methods=['POST'])
@login_required
@role_required(['tenant'])
def send_message(id):
    user = User.query.get(session['user_id'])
    message = request.form.get('message')
    
    if message:
        comm = Communication(
            request_id=id,
            sender_role='tenant',
            sender_name=user.full_name,
            message=message,
            timestamp=datetime.now()
        )
        db.session.add(comm)
        db.session.commit()
        flash('Message sent', 'success')
    
    return redirect(url_for('tenant.view_maintenance', id=id))

@tenant_bp.route('/rent')
@login_required
@role_required(['tenant'])
def rent():
    user = User.query.get(session['user_id'])
    tenant = Tenant.query.filter_by(user_id=user.id).first()
    
    payments = RentPayment.query.filter_by(tenant_id=tenant.id).order_by(RentPayment.due_date.desc()).all()
    
    return render_template('tenant/rent.html', tenant=tenant, payments=payments)

@tenant_bp.route('/notice', methods=['GET', 'POST'])
@login_required
@role_required(['tenant'])
def notice():
    user = User.query.get(session['user_id'])
    tenant = Tenant.query.filter_by(user_id=user.id).first()
    
    if request.method == 'POST':
        vacate_date = datetime.strptime(request.form.get('vacate_date'), '%Y-%m-%d')
        
        notice = Notice(
            tenant_id=tenant.id,
            vacate_date=vacate_date,
            status='pending',
            submitted_date=datetime.now()
        )
        db.session.add(notice)
        db.session.commit()
        
        flash('Notice to vacate submitted successfully', 'success')
        return redirect(url_for('tenant_dashboard'))
    
    existing_notice = Notice.query.filter_by(tenant_id=tenant.id, status='active').first()
    
    return render_template('tenant/notice.html', tenant=tenant, notice=existing_notice)

@tenant_bp.route('/messages')
@login_required
@role_required(['tenant'])
def messages():
    user = User.query.get(session['user_id'])
    tenant = Tenant.query.filter_by(user_id=user.id).first()
    
    # Get all communications for tenant's requests
    requests = MaintenanceRequest.query.filter_by(tenant_id=tenant.id).all()
    request_ids = [r.id for r in requests]
    
    communications = Communication.query.filter(
        Communication.request_id.in_(request_ids)
    ).order_by(Communication.timestamp.desc()).all()
    
    return render_template('tenant/messages.html', communications=communications)