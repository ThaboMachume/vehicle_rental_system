# Vehicle Rental Management System (VRMS)

A comprehensive web-based Vehicle Rental Management System built with Python Flask.

**Module:** NPRT 630 — Project  
**Group:** WEHATEBUGS  
**Student:** Thabo Machume — 202204405

## Features

- Role-Based Access Control (Administrator, Manager, Clerk)
- Customer Management with Rental History
- Vehicle Fleet Management
- Complete Rental Workflow (Book → Checkout → Return → Payment → Invoice)
- Automated Late Fee and Fuel Penalty Calculation
- VAT + Invoice Generation
- Rental Agreement Contract (Printable)
- Reports Dashboard with Interactive Charts
- User Management
- System Audit Logging
- System Alerts Panel
- Confirmation Dialogs for Destructive Actions
- Auto-logout after 15 minutes of inactivity
- Forgot Password flow

## Technology Stack

- **Backend:** Python 3 + Flask
- **Database:** SQLite via SQLAlchemy ORM
- **Authentication:** Flask-Login (bcrypt hashing)
- **Frontend:** Jinja2, Bootstrap 5, Chart.js

## Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/ThaboMachume/vehicle_rental_system.git
cd vehicle_rental_system
