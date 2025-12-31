# Notifications Module Documentation

## Overview

The **Notifications** module is a cross-cutting concern that keeps users informed about system events. It supports multi-channel alerts (In-App, Email) and handles both event-driven (real-time) and scheduled (cron-based) notifications.

## Core Responsibilities

1. **Event Notifications**: Immediate alerts for actions (e.g., "Claim Approved").
2. **Scheduled Reminders**: Time-based alerts (e.g., "Policy Expiring in 7 days").
3. **Template Management**: Centralized message formats.

---

## 2. Models

### `Notification`
The actual message record.
- **Fields**: `user`, `title`, `message`, `type` (e.g., POLICY_ISSUED).
- **Status**: `is_read`, `read_at`.
- **Channel**: `email_sent` status.

### `NotificationTemplate`
To avoid hardcoding strings in code, templates are stored in DB.
- **Example**:
  - Code: `CLAIM_APPROVED`
  - Body: `Dear {name}, your claim {claim_no} for ₹{amount} is approved.`

### `ScheduledReminder`
Queue for future notifications.
- Used for expiry warnings and renewal reminders.
- A background job polls this table to trigger actual notifications.

---

## 3. Architecture

### Service Layer
`NotificationService` provides a clean API for other modules:

```python
# Other modules just call this, ignoring implementation details
NotificationService.send_notification(
    user=customer,
    type='POLICY_ISSUED',
    context={'policy_no': 'POL-123'}
)
```

The service handles:
1. Fetching the template.
2. Rendering content with context variables.
3. Creating the database record (In-App).
4. Triggering the Email Service (Async).

### Integration Points
- **Policies**: Triggers 'Issued', 'Expiring', 'Renewed'.
- **Claims**: Triggers 'Submitted', 'Approved', 'Rejected', 'Settled'.
- **Applications**: Triggers 'Status Change'.
- **Auth**: Triggers 'Welcome', 'Password Reset'.
