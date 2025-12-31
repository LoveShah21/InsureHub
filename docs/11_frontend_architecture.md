# Frontend Architecture

## Overview

The frontend is built using **Django Templates** (Server-Side Rendering) enhanced with **JavaScript** for dynamic interactivity. This approach was chosen for SEO friendliness, faster initial load times, and simpler integration with Django's auth system compared to a decoupled SPA (Single Page Application).

---

## 1. Directory Structure

The `templates/` directory is organized by app/module to ensure maintainability.

```text
templates/
├── base.html                  # Master layout (Header, Footer, Nav)
├── components/                # Reusable snippets
│   ├── navbar.html
│   ├── sidebar.html
│   ├── footer.html
│   └── messages.html          # Toast notifications
├── auth/                      # Authentication pages
│   ├── login.html
│   └── register.html
├── backoffice/                # Staff dashboard
│   ├── dashboard.html
│   ├── applications/
│   │   ├── list.html
│   │   └── detail.html
│   └── ...
└── customer/                  # Customer portal
    ├── dashboard.html
    ├── policies/
    └── ...
```

---

## 2. Base Templates & Inheritance

We use the **Template Inheritance** pattern to obey DRY (Don't Repeat Yourself) principles.

### `base.html`
Defines the skeleton of the HTML document.
- Includes CSS (Bootstrap/Custom).
- Includes JS libraries (jQuery, Bootstrap JS).
- Defines blocks: `{% block content %}`, `{% block extra_css %}`, `{% block extra_js %}`.

### `backoffice_base.html` / `customer_base.html`
Extend `base.html` to add role-specific navigation bars and sidebars.

```django
{% extends 'base.html' %}

{% block content %}
<div class="d-flex">
    {% include 'components/sidebar.html' %}
    <main class="flex-grow-1">
        {% block dashboard_content %}{% endblock %}
    </main>
</div>
{% endblock %}
```

---

## 3. UI Framework & Styling

- **Framework**: Bootstrap 5 (Responsive Grid, Components).
- **Custom CSS**: `static/css/style.css` for branding (colors, fonts).
- **Icons**: FontAwesome or Bootstrap Icons.
- **Responsiveness**: All pages are designed to work on Mobile, Tablet, and Desktop.

---

## 4. Dynamic Interactions (JavaScript)

While pages are server-rendered, JavaScript is used for:

1. **Form Validation**: Client-side checks before submission.
2. **Dynamic Forms**:
   - *Example*: Selecting "Motor Insurance" dynamically shows "Vehicle Number" fields and hides "Patient Name" fields without page reload.
3. **AJAX Requests**:
   - Checking email uniqueness during registration.
   - Fetching updated quote prices when coverage is toggled.
4. **Dashboard Charts**: Using `Chart.js` to render analytics graphs (Backoffice Dashboard).
5. **Payment Integration**: `Razorpay Checkout.js` is embedded to handle the payment modal.

---

## 5. Context Processors

We use custom context processors to make common data available globally in templates:
- `user_role`: To conditionally render menu items (e.g., Hide "Admin Panel" link for Customers).
- `notification_count`: To show the unread badge count in the navbar.
