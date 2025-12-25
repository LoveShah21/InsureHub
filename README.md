# Intelligent Insurance Policy Management & Decision Support System

A comprehensive insurance policy management system built with Django and Django REST Framework for a final-year university project.

## Features

### Phase 1 - Foundation ✅
- **IAM Module**: Custom User model, Role-based access control (Admin, Backoffice, Customer)
- **JWT Authentication**: Secure token-based authentication
- **Insurance Catalog**: Insurance types, companies, coverages, add-ons
- **Customer Profiling**: Customer profiles with demographics

### Phase 2 - Core Business Logic ✅
- **Applications**: Insurance application submission with document upload
- **Quote Generation**: Rule-based scoring algorithm for quote comparison
- **Policy Issuance**: Mock payment gateway with policy generation
- **Claims Management**: Complete claim lifecycle (Submit → Review → Approve/Reject → Settle)

### Phase 3 - Partial Implementation ✅
- **Notifications**: In-app notifications for policy/claim events
- **Analytics Dashboard**: Live ORM-based metrics

### Phase 4 - Conceptual 📋
- **Renewal Prediction**: Schema and dummy prediction function (future ML scope)

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Django 4.2 + Django REST Framework |
| Database | MySQL |
| Auth | JWT (djangorestframework-simplejwt) |
| ORM | Django ORM (no raw SQL) |
| Payments | Mock Gateway (80% success rate) |

---

## Quote Scoring Algorithm

```
score = (0.4 × affordability) + (0.3 × claim_ratio) + 
        (0.2 × coverage) + (0.1 × service_rating)
```

| Component | Weight | Description |
|-----------|--------|-------------|
| Affordability | 40% | Premium vs customer budget/income |
| Claim Ratio | 30% | Insurance company's settlement ratio |
| Coverage | 20% | Completeness of selected coverages |
| Service Rating | 10% | Company's service quality rating |

---

## Quick Start

### Prerequisites
- Python 3.11+
- MySQL Server
- Git

### 1. Clone & Setup Virtual Environment
```bash
cd "insurance policy project"
python -m venv .venv
.\.venv\Scripts\activate  # Windows
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Database
Create MySQL database:
```sql
CREATE DATABASE insurance_db;
```

Update `.env` file with your MySQL credentials:
```env
DB_NAME=insurance_db
DB_USER=root
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=3306
```

### 4. Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Seed Initial Data
```bash
python manage.py seed_data
```
This creates:
- Default roles (ADMIN, BACKOFFICE, CUSTOMER)
- Admin user: `admin@insurance.local` / `Admin@12345`

### 6. Start Server
```bash
python manage.py runserver 8001
```

### 7. Access API
- **API Root**: http://127.0.0.1:8001/api/v1/
- **Admin Panel**: http://127.0.0.1:8001/admin/

---

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register/` | User registration |
| POST | `/api/v1/auth/login/` | Login (returns JWT) |
| POST | `/api/v1/auth/logout/` | Logout |
| POST | `/api/v1/auth/refresh/` | Refresh token |

### Applications
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/applications/` | Create application |
| POST | `/api/v1/applications/{id}/submit/` | Submit for review |
| POST | `/api/v1/applications/{id}/update-status/` | Backoffice status update |

### Quotes
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/quotes/generate/` | Generate quotes |
| GET | `/api/v1/quotes/compare/` | Compare with top-3 |
| POST | `/api/v1/quotes/{id}/accept/` | Accept quote |

### Policies & Payments
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/policies/` | List policies |
| POST | `/api/v1/payments/initiate/` | Initiate payment |

### Claims
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/claims/` | Submit claim |
| POST | `/api/v1/claims/{id}/update-status/` | Backoffice status update |

### Analytics
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/analytics/dashboard/` | Dashboard metrics |

---

## Project Structure

```
insurance policy project/
├── apps/
│   ├── accounts/       # IAM - Users, Roles, Permissions
│   ├── catalog/        # Insurance Types, Companies, Coverages
│   ├── customers/      # Customer Profiles
│   ├── applications/   # Insurance Applications
│   ├── quotes/         # Quote Generation + Scoring
│   ├── policies/       # Policy + Payment + Invoice
│   ├── claims/         # Claim Lifecycle
│   ├── notifications/  # User Notifications
│   └── analytics/      # Dashboard + Prediction
├── insurance_project/  # Django Project Settings
├── .env               # Environment Config
├── requirements.txt   # Dependencies
└── manage.py
```

---

## Implemented vs Conceptual Features

| Feature | Status | Notes |
|---------|--------|-------|
| User Authentication | ✅ Implemented | JWT-based |
| Role-Based Access | ✅ Implemented | Admin, Backoffice, Customer |
| Insurance Catalog | ✅ Implemented | Full CRUD |
| Applications | ✅ Implemented | With document upload |
| Quote Scoring | ✅ Implemented | Rule-based algorithm |
| Mock Payment | ✅ Implemented | 80% success rate |
| Claim Workflow | ✅ Implemented | Full lifecycle |
| Notifications | ✅ Implemented | Console logging |
| Analytics | ✅ Implemented | Live ORM aggregation |
| Renewal Prediction | 📋 Conceptual | Schema + dummy function |
| Email Sending | 📋 Conceptual | Logs only |

---

## License

This project is for academic purposes (Final Year University Project).

---

## Author

Built as part of the Intelligent Insurance Policy Management & Decision Support System project.
