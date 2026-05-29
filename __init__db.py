# init_db.py
from app import app, db
from models import User, Tenant, Landlord, PropertyManager, Technician, Property, Vacancy, MaintenanceRequest, Communication, RentPayment, Notice
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta

def init_database():
    """Initialize the database with tables and sample data"""
    
    with app.app_context():
        # Drop all tables (use with caution - this deletes all data)
        db.drop_all()
        
        # Create all tables
        db.create_all()
        
        print("Database tables created successfully!")
        
        # Create sample users
        print("Creating sample users...")
        
        # Admin / Property Manager
        admin_user = User(
            full_name="John Manager",
            email="manager@propmanage.com",
            phone="+254700000001",
            password=generate_password_hash("password123"),
            role="property_manager",
            is_active=True
        )
        db.session.add(admin_user)
        
        # Landlord
        landlord_user = User(
            full_name="Sarah Landlord",
            email="landlord@propmanage.com",
            phone="+254700000002",
            password=generate_password_hash("password123"),
            role="landlord",
            is_active=True
        )
        db.session.add(landlord_user)
        
        # Tenant
        tenant_user = User(
            full_name="Alex Johnson",
            email="tenant@propmanage.com",
            phone="+254700000003",
            password=generate_password_hash("password123"),
            role="tenant",
            is_active=True
        )
        db.session.add(tenant_user)
        
        # Technician 1
        tech1_user = User(
            full_name="Mike Wren",
            email="technician@propmanage.com",
            phone="+254700000004",
            password=generate_password_hash("password123"),
            role="technician",
            is_active=True
        )
        db.session.add(tech1_user)
        
        # Technician 2
        tech2_user = User(
            full_name="Sarah Chen",
            email="sarah.chen@propmanage.com",
            phone="+254700000005",
            password=generate_password_hash("password123"),
            role="technician",
            is_active=True
        )
        db.session.add(tech2_user)
        
        db.session.commit()
        
        # Create landlord profile
        landlord = Landlord(
            user_id=landlord_user.id,
            company_name="Prime Properties Ltd",
            tax_id="P100123456"
        )
        db.session.add(landlord)
        
        # Create property manager profile
        property_manager = PropertyManager(
            user_id=admin_user.id,
            department="Operations",
            employee_id="PM001"
        )
        db.session.add(property_manager)
        
        # Create property
        property1 = Property(
            name="Sunset Apartments",
            address="123 Main Street",
            city="Nairobi",
            state="Nairobi",
            zip_code="00100",
            total_units=20,
            landlord_id=landlord.id,
            manager_id=property_manager.id
        )
        db.session.add(property1)
        
        db.session.commit()
        
        # Create tenant profile
        tenant = Tenant(
            user_id=tenant_user.id,
            property_id=property1.id,
            unit_number="Apt 4B",
            monthly_rent=18500,
            balance=1250,  # Has arrears
            deposit_amount=18500,
            lease_start_date=datetime.now().date(),
            lease_end_date=datetime.now().date() + timedelta(days=365),
            emergency_contact_name="Jane Johnson",
            emergency_contact_phone="+254711223344"
        )
        db.session.add(tenant)
        
        # Create technician profiles
        technician1 = Technician(
            user_id=tech1_user.id,
            specialty="Plumbing & General",
            status="available",
            hourly_rate=500
        )
        db.session.add(technician1)
        
        technician2 = Technician(
            user_id=tech2_user.id,
            specialty="Electrical & HVAC",
            status="available",
            hourly_rate=600
        )
        db.session.add(technician2)
        
        db.session.commit()
        
        # Create vacancies
        vacancy1 = Vacancy(
            property_id=property1.id,
            unit_number="Apt 2A",
            property_name="Sunset Apartments",
            monthly_rent=17000,
            bedrooms=2,
            bathrooms=1,
            square_feet=850,
            status="vacant",
            description="Spacious 2-bedroom apartment with balcony"
        )
        db.session.add(vacancy1)
        
        vacancy2 = Vacancy(
            property_id=property1.id,
            unit_number="Studio 1C",
            property_name="Sunset Apartments",
            monthly_rent=14000,
            bedrooms=1,
            bathrooms=1,
            square_feet=550,
            status="vacant",
            description="Cozy studio apartment, perfect for singles"
        )
        db.session.add(vacancy2)
        
        # Create maintenance requests
        request1 = MaintenanceRequest(
            tenant_id=tenant.id,
            technician_id=technician1.id,
            title="Water heater leaking",
            description="The water heater in the bathroom is leaking water continuously. Need immediate attention.",
            unit_number="Apt 4B",
            property_name="Sunset Apartments",
            priority="urgent",
            status="in_progress",
            estimated_cost=3500,
            created_at=datetime.now() - timedelta(days=2),
            assigned_at=datetime.now() - timedelta(days=1)
        )
        db.session.add(request1)
        
        request2 = MaintenanceRequest(
            tenant_id=tenant.id,
            technician_id=technician2.id,
            title="AC not cooling",
            description="The air conditioner is running but not cooling the room properly.",
            unit_number="Apt 4B",
            property_name="Sunset Apartments",
            priority="normal",
            status="pending",
            estimated_cost=4500,
            created_at=datetime.now() - timedelta(days=5)
        )
        db.session.add(request2)
        
        db.session.commit()
        
        # Create communications
        comm1 = Communication(
            request_id=request1.id,
            sender_role="tenant",
            sender_name="Alex Johnson",
            message="The heater is leaking badly, please come as soon as possible",
            timestamp=datetime.now() - timedelta(days=2)
        )
        db.session.add(comm1)
        
        comm2 = Communication(
            request_id=request1.id,
            sender_role="technician",
            sender_name="Mike Wren",
            message="I'll arrive tomorrow morning with the necessary parts",
            timestamp=datetime.now() - timedelta(days=1)
        )
        db.session.add(comm2)
        
        comm3 = Communication(
            request_id=request2.id,
            sender_role="tenant",
            sender_name="Alex Johnson",
            message="The AC is making a weird noise, please check",
            timestamp=datetime.now() - timedelta(days=5)
        )
        db.session.add(comm3)
        
        comm4 = Communication(
            request_id=request2.id,
            sender_role="technician",
            sender_name="Sarah Chen",
            message="I've diagnosed the issue. It's a compressor problem. Estimated cost KSh 4,500",
            timestamp=datetime.now() - timedelta(days=4)
        )
        db.session.add(comm4)
        
        # Create rent payments
        payment1 = RentPayment(
            tenant_id=tenant.id,
            amount=18500,
            payment_date=datetime.now() - timedelta(days=30),
            due_date=datetime.now().date() - timedelta(days=25),
            method="mpesa",
            reference="MPESA123456",
            status="completed"
        )
        db.session.add(payment1)
        
        payment2 = RentPayment(
            tenant_id=tenant.id,
            amount=18500,
            payment_date=datetime.now() - timedelta(days=60),
            due_date=datetime.now().date() - timedelta(days=55),
            method="bank",
            reference="TRF789012",
            status="completed"
        )
        db.session.add(payment2)
        
        db.session.commit()
        
        print("Sample data created successfully!")
        print("\n=== Login Credentials ===")
        print("Property Manager: manager@propmanage.com / password123")
        print("Landlord: landlord@propmanage.com / password123")
        print("Tenant: tenant@propmanage.com / password123")
        print("Technician: technician@propmanage.com / password123")
        print("========================")
        
        print("\nDatabase initialization complete!")

if __name__ == "__main__":
    init_database()