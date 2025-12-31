# Notification Flow Sequence Diagram

## Overview

This document describes how notifications are triggered by system events, processed, and delivered to users via multiple channels (In-App, Email).

---

## 1. Notification Trigger Flow

```mermaid
sequenceDiagram
    participant Source as Event Source (Policy)
    participant Service as Notification Service
    participant Template as Notification Template
    participant Model as Notification Model

    Source->>Service: Trigger Event (POLICY_ISSUED)
    Service->>Template: Get Template (POLICY_ISSUED)
    Template-->>Service: Template Content
    Service->>Service: Render Content
    Service->>Model: Create In-App Notification
    Service->>Service: Send Email (Async)
```

---

## 2. Scheduled Reminder Flow (Cron Job)

```mermaid
sequenceDiagram
    participant Scheduler
    participant Reminder as Reminder Service
    participant Notif as Notification Service
    participant User

    Scheduler->>Reminder: 1. Run Daily Check
    Reminder->>Reminder: 2. Find Expiring Policies (<7d)
    
    loop For each policy
        Reminder->>Notif: 3. Send Notification (POLICY_EXPIRING)
        Notif->>User: 4. Trigger Email
    end
```

---

## 3. Notification Read Flow

```mermaid
sequenceDiagram
    participant Browser
    participant View as Notif. View
    participant DB as Database

    Browser->>View: 1. Click Notification
    View->>DB: 2. Update is_read=True, read_at=Now
    View->>View: 3. Redirect to Target
    View-->>Browser: 4. Show Page
```

---

## 4. Email Template Rendering

```python
# Conceptual Template Rendering
template_text = "Dear {name}, your policy {policy_number} is approved."
context = {
    "name": "John Doe",
    "policy_number": "POL-123"
}
# Result
"Dear John Doe, your policy POL-123 is approved."
```
