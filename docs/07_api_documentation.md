# API Documentation

## Overview

The system exposes a RESTful API using **Django REST Framework (DRF)**. These APIs are primarily used by the frontend for dynamic interactions (AJAX calls) and mobile app integration (future scope).

- **Base URL**: `/api/v1/`
- **Authentication**: Bearer Token (JWT)
- **Response Format**: JSON

---

## 1. Authentication Endpoints

### Login
**POST** `/auth/login/`

Authenticate user and receive JWT tokens.

**Request:**
```json
{
    "email": "customer@example.com",
    "password": "securepassword123"
}
```

**Response (200 OK):**
```json
{
    "refresh": "eyJ0eX...",
    "access": "eyJ0eX...",
    "user": {
        "id": 1,
        "email": "customer@example.com",
        "role": "CUSTOMER"
    }
}
```

### Refresh Token
**POST** `/auth/token/refresh/`

Get a new access token using a valid refresh token.

**Request:**
```json
{
    "refresh": "eyJ0eX..."
}
```

---

## 2. Catalog API (Read Only)

### List Insurance Types
**GET** `/catalog/types/`

**Response:**
```json
[
    {
        "id": 1,
        "name": "Motor Insurance",
        "code": "MOTOR"
    },
    {
        "id": 2,
        "name": "Health Insurance",
        "code": "HEALTH"
    }
]
```

---

## 3. Quote API

### Create Quote Request
**POST** `/quotes/generate/`

**Request:**
```json
{
    "application_id": 15,
    "company_id": 3,
    "coverages": [1, 4],
    "addons": [2]
}
```

**Response (201 Created):**
```json
{
    "quote_id": 101,
    "quote_number": "QT-2025-001",
    "premium_breakdown": {
        "base": 25000,
        "tax": 4500,
        "total": 29500
    },
    "score": 85.5
}
```

---

## 4. Claims API

### Submit Claim
**POST** `/claims/submit/`

**Request:**
```json
{
    "policy_id": 55,
    "claim_type": "ACCIDENT",
    "amount_requested": 50000,
    "description": "Car bumper damaged in collision",
    "incident_date": "2025-12-30"
}
```

### Get Claim Status
**GET** `/claims/{id}/status/`

**Response:**
```json
{
    "claim_id": 202,
    "status": "UNDER_REVIEW",
    "timeline": [
        {"status": "SUBMITTED", "date": "2025-12-30 10:00:00"},
        {"status": "UNDER_REVIEW", "date": "2025-12-30 14:00:00"}
    ]
}
```

---

## 5. Payment API

### Verify Payment
**POST** `/payments/verify/`

Verifies Razorpay signature and issues policy.

**Request:**
```json
{
    "razorpay_order_id": "order_Hj7...",
    "razorpay_payment_id": "pay_K8...",
    "razorpay_signature": "a1b2c3..."
}
```

**Response (200 OK):**
```json
{
    "status": "success",
    "policy_number": "POL-2025-123456",
    "message": "Payment verified and policy issued."
}
```

---

## 6. Error Codes

The API uses standard HTTP status codes:

- **200 OK**: Success
- **201 Created**: Resource created successfully
- **400 Bad Request**: Validation error (e.g., missing fields)
- **401 Unauthorized**: Invalid or missing JWT token
- **403 Forbidden**: Token valid but user lacks permission (Role check)
- **404 Not Found**: Resource does not exist
- **500 Internal Server Error**: Unhandled exception
