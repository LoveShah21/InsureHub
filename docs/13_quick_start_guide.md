# Quick Start & Deployment Guide

## Prerequisites

- **Python**: 3.8+
- **Database**: MySQL 5.7+ (or SQLite for dev)
- **OS**: Windows / Linux / MacOS
- **Internet**: Required for Razorpay API

---

## 1. Installation

### Clone the Repository
```bash
git clone https://github.com/loveshah21/InsureHub.git
cd InsureHub
```

### Virtual Environment (Recommended)
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 2. Configuration (`.env`)

Create a `.env` file in the root directory.

```properties
# Django Settings
DEBUG=True
SECRET_KEY=django-insecure-your-secret-key-here
ALLOWED_HOSTS=*

# Database (Optional - Defaults to SQLite if not set)
DB_NAME=insurehub_db
DB_USER=root
DB_PASSWORD=yourpassword
DB_HOST=localhost
DB_PORT=3306

# Razorpay (Test Credentials)
RAZORPAY_KEY_ID=rzp_test_1234567890
RAZORPAY_KEY_SECRET=your_test_secret_here

# Email (Console Backend for Dev)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

---

## 3. Database Setup

### Migrations
Apply the database schema:
```bash
python manage.py makemigrations
python manage.py migrate
```

### Seed Data (Crucial for Demo)
Populate the system with initial master data (Categories, Roles, Admin user):
```bash
python manage.py seed_data
```

---

## 4. Running the Server

Start the Django development server:
```bash
python manage.py runserver
```

Access the application at: `http://127.0.0.1:8000/`

---

## 5. Application Tour (Demo Steps)

1. **Admin Login**:
   - URL: `/auth/login/`
   - Email: `admin@example.com`
   - Password: `password123`
   - **Action**: Check Dashboard, Configuration.

2. **Customer Registration**:
   - Register a new user.
   - Complete Profile.

3. **Buy Policy**:
   - Login as Customer.
   - "New Application" → Select "Motor".
   - Submit.

4. **Process Application**:
   - Login as Backoffice (`staff@example.com` / `password123`).
   - Approve Application.
   - Generate Quote.

5. **Payment**:
   - Back to Customer.
   - Pay for Quote (Use Razorpay Test Card).
   - Verify "Policy Issued".

---

## 6. Deployment (Production)

For actual deployment (e.g., AWS EC2, Heroku):
1. Set `DEBUG=False`.
2. Use **Gunicorn** instead of `runserver`.
3. Use **Nginx** as reverse proxy.
4. Serve static files using `whitenoise` or web server.
