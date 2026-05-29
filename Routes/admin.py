from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from sqlalchemy import func
from models import db, User, Tenant, Property, MaintenanceRequest, Technician, Communication, RentPayment, Vacancy
from .auth import login_required, role_required
from datetime import datetime, timedelta

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
@login_required
@role_required(['landlord', 'property_manager'])
def dashboard():
    # Get statistics
    total_properties = Property.query.count()
    total_tenants = Tenant.query.count()
    vacant_units = Vacancy.query.filter_by(status='vacant').count()
    pending_maintenance = MaintenanceRequest.query.filter_by(status='pending').count()
    
    # Financial calculations
    monthly_income = db.session.query(db.func.sum(RentPayment.amount)).filter(
        RentPayment.payment_date >= datetime.now().replace(day=1)
    ).scalar() or 0
    
    total_arrears = db.session.query(db.func.sum(Tenant.balance)).scalar() or 0
    
    # Get vacancies
    vacancies = Vacancy.query.filter_by(status='vacant').all()
    
    # Get recent maintenance requests
    maintenance_requests = MaintenanceRequest.query.order_by(
        MaintenanceRequest.created_at.desc()
    ).limit(5).all()
    
    # Get tenants with arrears
    arrears_tenants = Tenant.query.filter(Tenant.balance > 0).all()
    
    # Get recent communications
    communications = Communication.query.order_by(
        Communication.timestamp.desc()
    ).limit(10).all()
    
    # Prepare data for template
    vacancies_list = []
    for vac in vacancies:
        vacancies_list.append({
            'id': vac.id,
            'unit_number': vac.unit_number,
            'property_name': vac.property_name,
            'monthly_rent': vac.monthly_rent,
            'bedrooms': vac.bedrooms
        })
    
    maintenance_list = []
    for req in maintenance_requests:
        tenant = User.query.get(req.tenant_id)
        technician = User.query.get(req.technician_id) if req.technician_id else None
        maintenance_list.append({
            'id': req.id,
            'tenant_name': tenant.full_name if tenant else 'Unknown',
            'unit_number': req.unit_number,
            'title': req.title,
            'status': req.status,
            'technician_name': technician.full_name if technician else 'Unassigned',
            'estimated_cost': req.estimated_cost,
            'created_at': req.created_at
        })
    
    arrears_list = []
    for tenant in arrears_tenants:
        user = User.query.get(tenant.user_id)
        months_behind = int(tenant.balance / tenant.monthly_rent) if tenant.monthly_rent > 0 else 0
        arrears_list.append({
            'id': tenant.id,
            'name': user.full_name if user else 'Unknown',
            'unit_number': tenant.unit_number,
            'monthly_rent': tenant.monthly_rent,
            'arrears': tenant.balance,
            'months_behind': months_behind
        })
    
    return render_template('admin/admin_dashboard.html',
                         total_properties=total_properties,
                         total_tenants=total_tenants,
                         vacant_units=vacant_units,
                         pending_maintenance=pending_maintenance,
                         monthly_income=monthly_income,
                         total_arrears=total_arrears,
                         vacancies=vacancies_list,
                         maintenance_requests=maintenance_list,
                         arrears_tenants=arrears_list,
                         communications=communications,
                         now=datetime.now())

@admin_bp.route('/maintenance')
@login_required
@role_required(['landlord', 'property_manager'])
def maintenance():
    status_filter = request.args.get('status', '')
    technician_filter = request.args.get('technician', '')
    
    query = MaintenanceRequest.query
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    if technician_filter:
        query = query.filter_by(technician_id=int(technician_filter))
    
    requests = query.order_by(MaintenanceRequest.created_at.desc()).all()
    technicians = Technician.query.all()
    
    # Enrich requests with user names
    requests_list = []
    for req in requests:
        tenant = User.query.get(req.tenant_id)
        technician = User.query.get(req.technician_id) if req.technician_id else None
        requests_list.append({
            'id': req.id,
            'tenant_name': tenant.full_name if tenant else 'Unknown',
            'unit_number': req.unit_number,
            'title': req.title,
            'description': req.description,
            'status': req.status,
            'technician_id': req.technician_id,
            'estimated_cost': req.estimated_cost,
            'image_url': req.image_url,
            'created_at': req.created_at
        })
    
    tech_list = []
    for tech in technicians:
        user = User.query.get(tech.user_id)
        tech_list.append({
            'id': tech.id,
            'name': user.full_name if user else 'Unknown',
            'specialty': tech.specialty
        })
    
    return render_template('admin/maintenance_admin.html', 
                         requests=requests_list, 
                         technicians=tech_list)

@admin_bp.route('/maintenance/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required(['landlord', 'property_manager'])
def view_maintenance(id):
    request_obj = MaintenanceRequest.query.get_or_404(id)
    tenant = User.query.get(request_obj.tenant_id)
    technician = User.query.get(request_obj.technician_id) if request_obj.technician_id else None
    communications = Communication.query.filter_by(request_id=id).order_by(Communication.timestamp.asc()).all()
    technicians = Technician.query.all()
    
    tech_list = []
    for tech in technicians:
        user = User.query.get(tech.user_id)
        tech_list.append({
            'id': tech.id,
            'name': user.full_name if user else 'Unknown',
            'specialty': tech.specialty
        })
    
    if request.method == 'POST':
        technician_id = request.form.get('technician_id')
        estimated_cost = request.form.get('estimated_cost')
        status = request.form.get('status')
        
        if technician_id:
            request_obj.technician_id = int(technician_id)
        if estimated_cost:
            request_obj.estimated_cost = float(estimated_cost)
        if status:
            request_obj.status = status
        
        db.session.commit()
        flash('Maintenance request updated successfully', 'success')
        return redirect(url_for('admin.view_maintenance', id=id))
    
    return render_template('admin/view_maintenance.html',
                         request=request_obj,
                         tenant=tenant,
                         technician=technician,
                         communications=communications,
                         technicians=tech_list)

@admin_bp.route('/maintenance/<int:id>/reassign', methods=['POST'])
@login_required
@role_required(['landlord', 'property_manager'])
def reassign_technician(id):
    request_obj = MaintenanceRequest.query.get_or_404(id)
    technician_id = request.form.get('technician_id')
    
    if technician_id:
        request_obj.technician_id = int(technician_id)
        db.session.commit()
        flash('Technician reassigned successfully', 'success')
    
    return redirect(url_for('admin.maintenance'))

@admin_bp.route('/vacancies')
@login_required
@role_required(['landlord', 'property_manager'])
def vacancies():
    vacancies = Vacancy.query.all()
    return render_template('admin/vacancies.html', vacancies=vacancies)

@admin_bp.route('/vacancies/add', methods=['POST'])
@login_required
@role_required(['landlord', 'property_manager'])
def add_vacancy():
    unit_number = request.form.get('unit_number')
    property_name = request.form.get('property_name')
    monthly_rent = float(request.form.get('monthly_rent', 0))
    bedrooms = int(request.form.get('bedrooms', 1))
    bathrooms = int(request.form.get('bathrooms', 1))
    
    vacancy = Vacancy(
        unit_number=unit_number,
        property_name=property_name,
        monthly_rent=monthly_rent,
        bedrooms=bedrooms,
        bathrooms=bathrooms,
        status='vacant'
    )
    db.session.add(vacancy)
    db.session.commit()
    
    flash('Vacancy added successfully', 'success')
    return redirect(url_for('admin.vacancies'))

@admin_bp.route('/vacancies/<int:id>/mark-rented')
@login_required
@role_required(['landlord', 'property_manager'])
def mark_rented(id):
    vacancy = Vacancy.query.get_or_404(id)
    vacancy.status = 'rented'
    db.session.commit()
    flash('Unit marked as rented', 'success')
    return redirect(url_for('admin.vacancies'))

@admin_bp.route('/vacancies/<int:id>/delete')
@login_required
@role_required(['landlord', 'property_manager'])
def delete_vacancy(id):
    vacancy = Vacancy.query.get_or_404(id)
    db.session.delete(vacancy)
    db.session.commit()
    flash('Vacancy deleted', 'success')
    return redirect(url_for('admin.vacancies'))

@admin_bp.route('/finance')
@login_required
@role_required(['landlord', 'property_manager'])
def finance():
    # Get last 6 months income
    months = []
    income_data = []
    
    for i in range(5, -1, -1):
        month_date = datetime.now().replace(day=1) - timedelta(days=30*i)
        month_name = month_date.strftime('%B')
        months.append(month_name)
        
        monthly_total = db.session.query(func.sum(RentPayment.amount)).filter(
            RentPayment.payment_date >= month_date,
            RentPayment.payment_date < month_date + timedelta(days=32)
        ).scalar() or 0
        income_data.append(monthly_total)
    
    # Income by property
    property_income = []
    properties = Property.query.all()
    for prop in properties:
        total = db.session.query(func.sum(RentPayment.amount)).join(Tenant).filter(
            Tenant.property_id == prop.id
        ).scalar() or 0
        property_income.append({'name': prop.name, 'income': total})
    
    # Recent payments
    recent_payments = RentPayment.query.order_by(RentPayment.payment_date.desc()).limit(10).all()
    
    total_income_ytd = db.session.query(func.sum(RentPayment.amount)).filter(
        RentPayment.payment_date >= datetime.now().replace(month=1, day=1)
    ).scalar() or 0
    
    expected_income = db.session.query(func.sum(Tenant.monthly_rent)).scalar() or 0
    
    collected = db.session.query(func.sum(RentPayment.amount)).filter(
        RentPayment.payment_date >= datetime.now().replace(day=1)
    ).scalar() or 0
    
    collection_rate = (collected / expected_income * 100) if expected_income > 0 else 0
    
    return render_template('admin/finance.html',
                         months=months,
                         income_data=income_data,
                         property_income=property_income,
                         recent_payments=recent_payments,
                         total_income_ytd=total_income_ytd,
                         expected_income=expected_income,
                         collection_rate=round(collection_rate, 2))

@admin_bp.route('/maintenance/<int:id>/comment', methods=['POST'])
@login_required
@role_required(['landlord', 'property_manager'])
def add_comment(id):
    message = request.form.get('message')
    if message:
        comment = Communication(
            request_id=id,
            sender_role=session['user_role'],
            sender_name=session['user_name'],
            message=message,
            timestamp=datetime.now()
        )
        db.session.add(comment)
        db.session.commit()
        flash('Comment added', 'success')
    
    return redirect(url_for('admin.view_maintenance', id=id))