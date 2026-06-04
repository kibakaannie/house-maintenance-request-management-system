# 🏠 House Maintenance Management System

A complete web-based property management platform connecting tenants, landlords, property managers, and technicians. Built with Python Flask, this system streamlines maintenance requests, rent tracking, communication, and financial management.

## ✨ Features

### 👤 Tenant Dashboard
- View rent status and payment history
- Submit maintenance requests with photo uploads
- Track request status (Pending → In Progress → Completed)
- See assigned technician name and phone number
- View admin/technician "viewed" status
- Send messages to property manager/landlord
- Browse vacant houses with unit numbers

### 👔 Property Manager / Landlord Dashboard
- Overview of properties, tenants, vacancies, and maintenance
- Approve/reject tenant registrations
- Assign technicians to maintenance requests (with phone number)
- View all tenant details (name, phone, unit number, house type)
- Manage properties and vacancies
- Track income with charts and property-wise breakdown
- Record rent payments
- View all communications

### 🔧 Technician Dashboard
- View assigned maintenance requests
- Update request status (In Progress / Completed)
- Add estimated cost and personal phone number
- See tenant contact and house number
- Communicate with tenants via messages

### 💬 Messaging System
- Threaded conversations between tenants, managers, and technicians
- Read/unread status
- Timestamped messages
- Role-based visibility

### 💰 Financial Tracking
- Total income calculation
- Monthly income chart (last 6 months)
- Income breakdown by property
- Recent payment history
- Record rent payments

### 🏢 Property & Vacancy Management
- Add/edit properties
- List vacancies with unit numbers, type (bedsitter, 1BR, 2BR, 3BR), floor, rent
- Filter vacancies by type
- Mark units as rented

### 🔐 Security & Access Control
- Role-based authentication (tenant, landlord, property_manager, technician)
- Session-based login with password hashing (Werkzeug)
- Admin approval required for tenant registration
- Route protection for each role

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.x, Flask |
| Database | JSON files (users.json, requests.json, payments.json, messages.json, technicians.json) |
| Frontend | HTML5, CSS3, JavaScript |
| Icons | Font Awesome 6 |
| Authentication | Flask sessions, Werkzeug password hashing |

## 📁 Project Structure
