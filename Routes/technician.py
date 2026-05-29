from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import db, User, Technician, MaintenanceRequest, Communication
from .auth import login_required, role_required
from datetime import datetime

technician_bp = Blueprint('technician', __name__)

@technician_bp.route('/dashboard')
@login_required
@role_required(['technician'])
def dashboard():
    user = User.query.get(session['user_id'])
    technician = Technician.query.filter_by(user_id=user.id).first()
    
    # Get assigned requests
    assigned_requests = MaintenanceRequest.query.filter_by(technician_id=technician.id).order_by(
        MaintenanceRequest.created_at.desc()
    ).all()
    
    # Statistics
    pending_count = len([r for r in assigned_requests if r.status == 'pending'])
    in_progress_count = len([r for r in assigned_requests if r.status == 'in_progress'])
    completed_count = len([r for r in assigned_requests if r.status == 'completed'])
    
    return render_template('technician/technician_dashboard.html',
                         technician=technician,
                         requests=assigned_requests,
                         pending_count=pending_count,
                         in_progress_count=in_progress_count,
                         completed_count=completed_count,
                         current_user=user)

@technician_bp.route('/requests')
@login_required
@role_required(['technician'])
def requests():
    user = User.query.get(session['user_id'])
    technician = Technician.query.filter_by(user_id=user.id).first()
    
    status_filter = request.args.get('status', '')
    
    query = MaintenanceRequest.query.filter_by(technician_id=technician.id)
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    requests = query.order_by(MaintenanceRequest.created_at.desc()).all()
    
    return render_template('technician/my_requests.html', requests=requests)

@technician_bp.route('/request/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required(['technician'])
def view_request(id):
    user = User.query.get(session['user_id'])
    technician = Technician.query.filter_by(user_id=user.id).first()
    request_obj = MaintenanceRequest.query.get_or_404(id)
    
    # Verify assignment
    if request_obj.technician_id != technician.id:
        flash('Access denied', 'danger')
        return redirect(url_for('technician_dashboard'))
    
    tenant = User.query.get(request_obj.tenant_id)
    communications = Communication.query.filter_by(request_id=id).order_by(Communication.timestamp.asc()).all()
    
    if request.method == 'POST':
        # Update status
        new_status = request.form.get('status')
        if new_status:
            request_obj.status = new_status
        
        # Update estimated cost
        estimated_cost = request.form.get('estimated_cost')
        if estimated_cost:
            request_obj.estimated_cost = float(estimated_cost)
        
        db.session.commit()
        
        # Add system message about update
        comm = Communication(
            request_id=id,
            sender_role='technician',
            sender_name=user.full_name,
            message=f"Request updated: Status changed to {new_status}" + (f", estimated cost KSh {estimated_cost}" if estimated_cost else ""),
            timestamp=datetime.now()
        )
        db.session.add(comm)
        db.session.commit()
        
        flash('Request updated successfully', 'success')
        return redirect(url_for('technician.view_request', id=id))
    
    return render_template('technician/request_detail.html',
                         request=request_obj,
                         tenant=tenant,
                         communications=communications)

@technician_bp.route('/request/<int:id>/message', methods=['POST'])
@login_required
@role_required(['technician'])
def send_message(id):
    user = User.query.get(session['user_id'])
    message = request.form.get('message')
    
    if message:
        comm = Communication(
            request_id=id,
            sender_role='technician',
            sender_name=user.full_name,
            message=message,
            timestamp=datetime.now()
        )
        db.session.add(comm)
        db.session.commit()
        flash('Message sent to tenant', 'success')
    
    return redirect(url_for('technician.view_request', id=id))

@technician_bp.route('/update-cost/<int:id>', methods=['POST'])
@login_required
@role_required(['technician'])
def update_cost(id):
    user = User.query.get(session['user_id'])
    technician = Technician.query.filter_by(user_id=user.id).first()
    request_obj = MaintenanceRequest.query.get_or_404(id)
    
    if request_obj.technician_id != technician.id:
        flash('Access denied', 'danger')
        return redirect(url_for('technician_dashboard'))
    
    estimated_cost = request.form.get('estimated_cost')
    if estimated_cost:
        request_obj.estimated_cost = float(estimated_cost)
        db.session.commit()
        
        # Add communication
        comm = Communication(
            request_id=id,
            sender_role='technician',
            sender_name=user.full_name,
            message=f"Estimated repair cost: KSh {estimated_cost}",
            timestamp=datetime.now()
        )
        db.session.add(comm)
        db.session.commit()
        
        flash('Cost estimate updated', 'success')
    
    return redirect(url_for('technician.view_request', id=id))

@technician_bp.route('/update-status/<int:id>', methods=['POST'])
@login_required
@role_required(['technician'])
def update_status(id):
    user = User.query.get(session['user_id'])
    technician = Technician.query.filter_by(user_id=user.id).first()
    request_obj = MaintenanceRequest.query.get_or_404(id)
    
    if request_obj.technician_id != technician.id:
        flash('Access denied', 'danger')
        return redirect(url_for('technician_dashboard'))
    
    new_status = request.form.get('status')
    if new_status:
        request_obj.status = new_status
        db.session.commit()
        
        # Add communication
        comm = Communication(
            request_id=id,
            sender_role='technician',
            sender_name=user.full_name,
            message=f"Request status updated to: {new_status.replace('_', ' ').capitalize()}",
            timestamp=datetime.now()
        )
        db.session.add(comm)
        db.session.commit()
        
        flash('Status updated', 'success')
    
    return redirect(url_for('technician.view_request', id=id))

@technician_bp.route('/update-status', methods=['POST'])
@login_required
@role_required(['technician'])
def update_availability():
    """Update technician's availability status"""
    user = User.query.get(session['user_id'])
    technician = Technician.query.filter_by(user_id=user.id).first()

    new_status = request.form.get('status')
    if new_status in ['available', 'busy']:
        technician.status = new_status
        db.session.commit()
        flash(f'Your status has been updated to {new_status}', 'success')

    return redirect(url_for('technician_dashboard'))