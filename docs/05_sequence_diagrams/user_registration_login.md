# User Registration and Login Sequence Diagram

## Overview

This document describes the authentication flow including user registration, login with JWT token generation, and account lockout mechanism.

---

## 1. User Registration Flow

```mermaid
sequenceDiagram
    participant Browser
    participant API as Registration API
    participant Serializer as User Serializer
    participant DB as Database
    participant Email as Email Service

    Browser->>API: POST /api/register/ {data}
    API->>Serializer: Validate Data
    
    alt Data Invalid
        Serializer-->>API: Errors (400)
        API-->>Browser: JSON Error Response
    else Data Valid
        Serializer->>DB: Save User (is_active=True)
        DB-->>Serializer: User Object
        Serializer->>DB: Create Customer/Officer Profile
        Serializer->>Email: Send Welcome Email
        Serializer-->>API: Success Data
        API-->>Browser: 201 Created {user_id...}
    end
```

### Registration Validation Rules

| Field | Validation | Error Message |
|-------|-----------|---------------|
| email | Unique, valid format | "Email already registered" |
| username | Unique, alphanumeric | "Username already taken" |
| password | Min 8 chars | "Password too short" |
| password_confirm | Must match password | "Passwords do not match" |

---

## 2. User Login Flow (JWT)

```mermaid
sequenceDiagram
    participant Client
    participant API as TokenObtainView
    participant Auth as Authenticate
    participant JWT as JWT Handler
    participant DB as Database

    Client->>API: POST /api/token/ {user, pass}
    API->>Auth: Authenticate(credentials)
    Auth->>DB: Check User & Password
    
    alt Invalid Credentials
        DB-->>Auth: None
        Auth-->>API: AuthenticationFailed
        API-->>Client: 401 Unauthorized
    else Valid Credentials
        DB-->>Auth: User Object
        
        alt Account Locked?
            Auth->>DB: Check Failed Attempts
            DB-->>Auth: Locked / Not Locked
        end
        
        Auth-->>API: User
        API->>JWT: Refresh.for_user(user)
        JWT-->>API: Access & Refresh Tokens
        API-->>Client: 200 OK {access, refresh}
    end
```

### JWT Token Structure

```json
{
  "access_token": {
    "token_type": "access",
    "exp": 1704067200,  // 30 minutes from now
    "user_id": 123,
    "email": "customer@example.com"
  },
  "refresh_token": {
    "token_type": "refresh",
    "exp": 1704672000,  // 7 days from now
    "user_id": 123
  }
}
```

---

## 3. Failed Login and Account Lockout

```
┌────────────┐     ┌────────────┐     ┌────────────┐     ┌────────────┐
│   Browser  │     │  AuthView  │     │   User     │     │  Config    │
│            │     │            │     │   Model    │     │            │
└─────┬──────┘     └─────┬──────┘     └─────┬──────┘     └─────┬──────┘
      │                  │                  │                  │
      │ POST {email,     │                  │                  │
      │   wrong_password}│                  │                  │
      ├─────────────────►│                  │                  │
      │                  │                  │                  │
      │                  │ check_password() │                  │
      │                  ├─────────────────►│                  │
      │                  │                  │                  │
      │                  │ False            │                  │
      │                  │◄─────────────────┤                  │
      │                  │                  │                  │
      │                  │ record_failed_   │                  │
      │                  │ login()          │                  │
      │                  ├─────────────────►│                  │
      │                  │                  │                  │
      │                  │                  │ failed_attempts++│
      │                  │                  ├─────────┐        │
      │                  │                  │◄────────┘        │
      │                  │                  │                  │
      │                  │                  │ Get threshold    │
      │                  │                  ├─────────────────►│
      │                  │                  │                  │
      │                  │                  │ LOCK_THRESHOLD=5 │
      │                  │                  │◄─────────────────┤
      │                  │                  │                  │
      │                  │                  │ [If attempts ≥ 5]│
      │                  │                  │ lock_account()   │
      │                  │                  ├─────────┐        │
      │                  │                  │◄────────┘        │
      │                  │                  │                  │
      │                  │ Updated count    │                  │
      │                  │◄─────────────────┤                  │
      │                  │                  │                  │
      │ Error: Invalid   │                  │                  │
      │ credentials      │                  │                  │
      │ (4 attempts left)│                  │                  │
      │◄─────────────────┤                  │                  │
      │                  │                  │                  │
```

### Account Lockout Logic

```python
# In User model (apps/accounts/models.py)

def is_account_locked(self):
    """Check if account is currently locked."""
    if self.account_locked_until:
        if timezone.now() < self.account_locked_until:
            return True
        else:
            # Lock expired, reset
            self.account_locked_until = None
            self.failed_login_attempts = 0
            self.save()
    return False

def record_failed_login(self):
    """Record failed login attempt."""
    self.failed_login_attempts += 1
    threshold = BusinessConfiguration.get_int('ACCOUNT_LOCK_THRESHOLD', 5)
    
    if self.failed_login_attempts >= threshold:
        self.lock_account()
    self.save()

def lock_account(self, duration_minutes=30):
    """Lock the account for specified duration."""
    self.account_locked_until = timezone.now() + timedelta(minutes=duration_minutes)
    self.save()
```

---

## 4. Role-Based Redirect After Login

```mermaid
flowchart TD
    Login[User Logs In] --> CheckRole{Check Role}
    CheckRole -- CUSTOMER --> Red1[Redirect to<br/>/dashboard/customer/]
    CheckRole -- BACKOFFICE --> Red2[Redirect to<br/>/dashboard/backoffice/]
    CheckRole -- ADMIN --> Red3[Redirect to<br/>/dashboard/admin/]
```

### Code Reference

```python
# In apps/accounts/mixins.py

def get_dashboard_url(user):
    """Get appropriate dashboard URL for user based on role."""
    if has_role(user, 'ADMIN'):
        return '/panel/dashboard/'
    elif has_role(user, 'BACKOFFICE'):
        return '/backoffice/dashboard/'
    elif has_role(user, 'CUSTOMER'):
        return '/customer/dashboard/'
    return '/auth/login/'
```

---

## 5. API Authentication Flow (JWT)

```mermaid
sequenceDiagram
    participant Client
    participant Middleware
    participant View
    participant Permission

    Client->>Middleware: GET /api/secure-data/<br/>Header: Bearer eyJ...
    Middleware->>Middleware: Decode & Verify Token
    
    alt Token Invalid
        Middleware-->>Client: 401 Unauthorized
    else Token Valid
        Middleware->>View: Request (user attached)
        View->>Permission: HasPermission(user)
        
        alt Denied
            Permission-->>View: False
            View-->>Client: 403 Forbidden
        else Allowed
            Permission-->>View: True
            View-->>View: Process Logic
            View-->>Client: 200 OK
        end
    end
```

---

## 6. Token Refresh Flow

```mermaid
sequenceDiagram
    participant Client
    participant API as TokenRefreshView
    participant JWT

    Client->>API: POST /api/token/refresh/<br/>{refresh: "..."}
    API->>JWT: Verify Refresh Token
    
    alt Token Invalid/Expired
        JWT-->>API: Error
        API-->>Client: 401 Unauthorized
    else Token Valid
        JWT->>JWT: Generate New Access Token
        JWT-->>API: New Access Token
        API-->>Client: 200 OK {access: "new..."}
    end
```

---

## 7. Logout Flow

```mermaid
sequenceDiagram
    participant Browser
    participant API as LogoutView
    participant Audit as AuditLog

    Browser->>API: GET /auth/logout/
    API->>Audit: Log LOGOUT action
    API->>API: Clear session
    API->>API: Invalidate JWT (blacklist)
    API-->>Browser: Clear cookies + Redirect /login
```
