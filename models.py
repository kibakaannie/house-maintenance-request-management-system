# models.py
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base 
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text
from app import db
from app import login_manager
from werkzeug.security import generate_password_hash, check_password_hash   
from flask_login import UserMixin
from datetime import datetime
from sqlalchemy import func
from datetime import datetime
from flask_login import UserMixin

db = SQLAlchemy()

# Association Tables
class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # tenant, landlord, property_manager, technician
    profile_picture = db.Column(db.String(200), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tenant_profile = db.relationship('Tenant', backref='user', uselist=False, cascade='all, delete-orphan')
    landlord_profile = db.relationship('Landlord', backref='user', uselist=False, cascade='all, delete-orphan')
    property_manager_profile = db.relationship('PropertyManager', backref='user', uselist=False, cascade='all, delete-orphan')
    technician_profile = db.relationship('Technician', backref='user', uselist=False, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.full_name}>'

class Tenant(db.Model):
    __tablename__ = 'tenants'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'), nullable=True)
    unit_number = db.Column(db.String(50), nullable=False)
    monthly_rent = db.Column(db.Float, default=0)
    balance = db.Column(db.Float, default=0)  # Rent arrears
    deposit_amount = db.Column(db.Float, default=0)
    lease_start_date = db.Column(db.Date, nullable=True)
    lease_end_date = db.Column(db.Date, nullable=True)
    emergency_contact_name = db.Column(db.String(100), nullable=True)
    emergency_contact_phone = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    maintenance_requests = db.relationship('MaintenanceRequest', backref='tenant', lazy=True, cascade='all, delete-orphan')
    rent_payments = db.relationship('RentPayment', backref='tenant', lazy=True, cascade='all, delete-orphan')
    notices = db.relationship('Notice', backref='tenant', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Tenant {self.unit_number}>'

class Landlord(db.Model):
    __tablename__ = 'landlords'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    company_name = db.Column(db.String(100), nullable=True)
    tax_id = db.Column(db.String(50), nullable=True)
    bank_account = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    properties = db.relationship('Property', backref='landlord', lazy=True)

class PropertyManager(db.Model):
    __tablename__ = 'property_managers'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    department = db.Column(db.String(100), nullable=True)
    employee_id = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    managed_properties = db.relationship('Property', backref='manager', lazy=True)

class Technician(db.Model):
    __tablename__ = 'technicians'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    specialty = db.Column(db.String(100), nullable=True)  # Plumbing, Electrical, HVAC, etc.
    status = db.Column(db.String(20), default='available')  # available, busy
    hourly_rate = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    assigned_requests = db.relationship('MaintenanceRequest', backref='technician', lazy=True, foreign_keys='MaintenanceRequest.technician_id')
    
    def __repr__(self):
        return f'<Technician {self.specialty}>'

class Property(db.Model):
    __tablename__ = 'properties'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    city = db.Column(db.String(50), nullable=False)
    state = db.Column(db.String(50), nullable=False)
    zip_code = db.Column(db.String(20), nullable=False)
    total_units = db.Column(db.Integer, default=0)
    landlord_id = db.Column(db.Integer, db.ForeignKey('landlords.id'), nullable=True)
    manager_id = db.Column(db.Integer, db.ForeignKey('property_managers.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tenants = db.relationship('Tenant', backref='property', lazy=True)
    vacancies = db.relationship('Vacancy', backref='property', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Property {self.name}>'

class Vacancy(db.Model):
    __tablename__ = 'vacancies'
    
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'), nullable=False)
    unit_number = db.Column(db.String(50), nullable=False)
    property_name = db.Column(db.String(100), nullable=False)
    monthly_rent = db.Column(db.Float, default=0)
    bedrooms = db.Column(db.Integer, default=1)
    bathrooms = db.Column(db.Integer, default=1)
    square_feet = db.Column(db.Integer, nullable=True)
    status = db.Column(db.String(20), default='vacant')  # vacant, rented, under_maintenance
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Vacancy {self.unit_number}>'

class MaintenanceRequest(db.Model):
    __tablename__ = 'maintenance_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    technician_id = db.Column(db.Integer, db.ForeignKey('technicians.id'), nullable=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    unit_number = db.Column(db.String(50), nullable=False)
    property_name = db.Column(db.String(100), nullable=True)
    priority = db.Column(db.String(20), default='normal')  # normal, urgent, emergency
    status = db.Column(db.String(20), default='pending')  # pending, in_progress, completed, cancelled
    estimated_cost = db.Column(db.Float, nullable=True)
    actual_cost = db.Column(db.Float, nullable=True)
    image_url = db.Column(db.String(200), nullable=True)
    completion_notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    assigned_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    communications = db.relationship('Communication', backref='request', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<MaintenanceRequest {self.title}>'

class Communication(db.Model):
    __tablename__ = 'communications'
    
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('maintenance_requests.id'), nullable=False)
    sender_role = db.Column(db.String(50), nullable=False)  # tenant, technician, admin
    sender_name = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Communication {self.id}>'

class RentPayment(db.Model):
    __tablename__ = 'rent_payments'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.Date, nullable=False)
    method = db.Column(db.String(50), nullable=False)  # mpesa, bank, cash, card
    reference = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(20), default='pending')  # pending, completed, failed
    receipt_url = db.Column(db.String(200), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @property
    def balance(self):
        # Calculate remaining balance for this payment period
        return self.amount - (self.amount if self.status == 'completed' else 0)
    
    def __repr__(self):
        return f'<RentPayment {self.amount}>'

class Notice(db.Model):
    __tablename__ = 'notices'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    vacate_date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected, cancelled
    submitted_date = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    admin_notes = db.Column(db.Text, nullable=True)
    
    def __repr__(self):
        return f'<Notice {self.id}>'

class Invoice(db.Model):
    __tablename__ = 'invoices'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    invoice_number = db.Column(db.String(50), unique=True, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='unpaid')  # unpaid, paid, overdue
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    paid_at = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f'<Invoice {self.invoice_number}>'

class Expense(db.Model):
    __tablename__ = 'expenses'
    
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'), nullable=True)
    category = db.Column(db.String(50), nullable=False)  # maintenance, utilities, taxes, insurance
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=True)
    expense_date = db.Column(db.Date, nullable=False)
    receipt_url = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Expense {self.amount}>'