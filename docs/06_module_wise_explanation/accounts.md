# Accounts Module Documentation

## Overview

The **Accounts** module handles Identity and Access Management (IAM). It acts as the foundation for the entire system, managing authentication, authorization, roles, and audit logging.

## Core Responsibilities

1. **User Management**: Registration, profile updates, account activation/deactivation.
2. **Authentication**: JWT-based login, secure password handling, session management.
3. **Authorization**: Role-Based Access Control (RBAC) enforcing permissions.
4. **Audit Logging**: Immutable tracking of critical system actions.

---

## 2. Models

### `User`
Custom user model extending Django's `AbstractUser`.

- **Key Fields**:
  - `email`: Used as the username for login (unique).
  - `failed_login_attempts`: Counter for brute-force protection.
  - `account_locked_until`: Timestamp for temporary lockout.
  - `phone_number`: Contact detail.

### `Role`
Defines system roles.

- **Predefined Roles**:
  - `ADMIN`: Full system access.
  - `BACKOFFICE`: Operational access (approvals, reviews).
  - `CUSTOMER`: End-user access.

### `UserRole`
Junction table managing M:N relationship between Users and Roles. Allows a user to hold multiple roles (e.g., a Backoffice user could also be a Customer).

### `AuditLog`
Records system activities for security and compliance.

- **Captured Data**:
  - `action_type`: INSERT, UPDATE, DELETE, LOGIN.
  - `table_name` & `record_id`: Target entity.
  - `old_values` & `new_values`: JSON snapshots of changes.
  - `ip_address`: Source IP.

---

## 3. Security Implementation

### Authentication (JWT)
The system uses JSON Web Tokens (JWT) for stateless authentication.
- **Access Token**: Short-lived (e.g., 30 mins), used for API requests.
- **Refresh Token**: Long-lived (e.g., 7 days), used to generate new access tokens.

### Account Lockout Mechanism
To prevent brute-force attacks:
1. Track `failed_login_attempts` on the user record.
2. If attempts ≥ `ACCOUNT_LOCK_THRESHOLD` (config), lock account.
3. Set `account_locked_until` to `now + 30 minutes`.
4. Reject login attempts until lock expires.

### Role-Based Access Control (RBAC)
Permissions are enforced using mixins and decorators.

**Key Permissions Classes (`apps/accounts/permissions.py`):**
- `IsAdmin`: Only users with ADMIN role.
- `IsBackoffice`: Users with BACKOFFICE or ADMIN role.
- `IsCustomer`: Users with CUSTOMER role.
- `IsOwnerOrAdmin`: Object-level permission (users can only see their own data).

---

## 4. Key Services & Utilities

### `RoleCheckMixin`
A view mixin that verifies if the current user has the required roles before dispatching the request.

```python
class AdminRequiredMixin(LoginRequiredMixin, RoleCheckMixin):
    required_roles = ['ADMIN']
```

### Audit Logging
Implemented via signals or explicit service calls. Any critical state change (e.g., claiming approval, policy issuance) creates an audit entry.

---

## 5. View Architecture

- **Auth Views**: `RegisterView`, `LoginView`, `LogoutView`.
- **Panel Views**: Dashboard views tailored by role (`/panel/`, `/backoffice/`, `/customer/`).
- **Redirect Logic**: Post-login, users are redirected to their specific dashboard based on their highest privilege role.
