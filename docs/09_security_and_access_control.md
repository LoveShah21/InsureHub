# Security Implementation

## Overview

Security is a paramount concern for an Insurance Policy Management System handling sensitive personal (PII) and financial data. This document outlines the multi-layered security architecture implemented in the project.

---

## 1. Authentication & Authorization

### JWT (JSON Web Tokens)
- **Stateful vs Stateless**: We use stateless JWT authentication for API communications. This avoids server-side session storage scalability issues.
- **Token Split**:
  - **Access Tokens**: Short lifespan (e.g., 30 minutes) to minimize risk if stolen.
  - **Refresh Tokens**: Longer lifespan (e.g., 7 days) stored securely to renew access.
- **Blacklisting**: On logout, tokens are blacklisted (if using Redis/DB backed blacklist) to prevent reuse.

### Role-Based Access Control (RBAC)
- **Middleware Enforcement**: Custom mixins (`AdminRequiredMixin`) ensure that unauthorized users cannot simply navigate to admin URLs.
- **Object-Level Permissions**: Users generally can only view *their own* data (`IsOwner` permission), preventing IDOR (Insecure Direct Object Reference) attacks.

```python
# Example of IDOR prevention
def get_queryset(self):
    return Claim.objects.filter(customer__user=self.request.user)
```

### Brute Force Protection
- **Account Lockout**: As detailed in `Accounts` module, 5 failed attempts lock the account for 30 minutes.
- **Rate Limiting**: (Optional config) Nginx or DRF throttling can limit requests per minute per IP.

---

## 2. Data Protection

### Encryption at Rest (Database)
- **Passwords**: Hashed using **PBKDF2-SHA256** with salt (Standard Django behavior). No plain text passwords are stored.
- **PII Masking**: Sensitive fields like PAN or Aadhaar can be masked in the frontend (`XXXX-1234`) and only revealed to authorized personnel.

### Encryption in Transit
- **HTTPS/SSL**: All production traffic must be served over HTTPS.
- **Secure Cookies**: `SESSION_COOKIE_SECURE` and `CSRF_COOKIE_SECURE` flags are enabled in production settings.

---

## 3. Web Vulnerability Mitigation

### CSRF (Cross-Site Request Forgery)
- **Django CSRF Token**: All POST forms include `{% csrf_token %}`.
- **Enforcement**: Middleware validates the token for every session-based state-changing request.

### XSS (Cross-Site Scripting)
- **Template Auto-escaping**: Django templates automatically escape variable output, converting `<script>` to `&lt;script&gt;`.
- **Content Security Policy (CSP)**: (Recommended) Headers to restrict script sources.

### SQL Injection
- **ORM Usage**: The system uses Django ORM for 99% of queries. Parameterization is handled automatically, neutralizing SQL injection attempts.
- **Raw SQL**: Avoided entirely or used with strict parameter binding if necessary.

---

## 4. Payment Security

### Signature Verification
As detailed in the Payment Sequence Diagram, we trust **no** data coming from the client browser regarding payment success. We verify the **cryptographic signature** provided by Razorpay server-side before issuing any policy.

```python
# Critical Security Check
if computed_signature != received_signature:
    raise SecurityException("Potential Payment Tampering Detected")
```

---

## 5. Audit Trails

Every significant write operation (Create, Update, Delete) is logged in the `AuditLog` table.
- **Who**: User ID
- **What**: Action and Table
- **When**: Timestamp
- **From**: IP Address

This ensures non-repudiation—administrators cannot deny actions they performed.
