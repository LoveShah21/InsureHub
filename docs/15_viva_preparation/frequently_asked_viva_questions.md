# Viva Voce Preparation Guide

## 1. Common Examiner Questions & Answers

### Q1: What is the core architecture of your project?
**A:** The project uses a **Monolithic Architecture** with a **Service Layer Design Pattern**. It is built on **Django**. We follow the **MVT (Model-View-Template)** pattern but decouple business logic into `services.py` to keep views thin. We also use a **Configuration-Driven** approach for business rules (e.g., Premium Slabs, Discounts) to allow changing logic without code deploys.

### Q2: How is the database normalized?
**A:** The database is normalized up to **BCNF (Boyce-Codd Normal Form)**.
- **1NF**: All fields are atomic.
- **2NF**: No partial dependencies (Composite keys handled correctly).
- **3NF**: No transitive dependencies (e.g., Company address is in `InsuranceCompany`, not `Quote`).
*Defense*: We intentionally denormalized `customer_id` in the `Quotes` table to optimize read performance for the "My Quotes" dashboard, accepting the redundancy for speed.

### Q3: How do you handle concurrency? (e.g., Two users accepting the same limited offer)
**A:** While this is a common issue, our use case relies on Database **ACID properties**.
- **Atomicity**: Payment and Policy Creation happen in a atomic transaction block (`transaction.atomic`). If policy creation fails, payment is rolled back (logically).
- **Isolation**: Row locking can be used (e.g., `select_for_update`) if we were managing limited stock inventories, though insurance is generally unlimited digital inventory.

### Q4: Explain the Security measures you implemented.
**A:**
1. **JWT Auth**: Stateless API authentication.
2. **CSRF & XSS**: Django's built-in middlewares.
3. **Signature Verification**: Crucial for Payments. We verify the HMAC-SHA256 signature from Razorpay to prevent tampering.
4. **RBAC**: Custom permissions (`IsAdmin`, `IsBackoffice`) enforcing authorization.

### Q5: How is the Premium calculated?
**A:** It uses a pipeline pattern:
`Base Premium (Slab)` + `Coverages` + `Addons` ± `Risk Loading (Profile)` - `Discounts (Rules)` + `GST`.
*Highlight*: Mention the "Scoring Engine" which is a unique feature that evaluates the *quality* of the quote, not just the price.

---

## 2. Key Code Snippets to Show

Have these ready to explain logic:

1. **`services.py` (Quote Logic)**: Show how you iterate through components to build the price.
2. **`payment_gateway.py`**: Show the `hmac` verification code.
3. **`models.py` (JSON Fields)**: Show how `application_data` stores dynamic JSON to support different insurance types.

---

## 3. Project Challenges & Solutions

| Challenge | Solution |
|-----------|----------|
| **Dynamic Forms**: Different insurance types need different data (Car no vs Patient age). | Use **JSONField** and dynamic frontend rendering based on Type. |
| **Complex Pricing**: Hardcoding prices makes the system rigid. | Implemented **Configuration Models** (`PremiumSlab`, `DiscountRule`) to store logic in DB. |
| **Payment Security**: Trusting frontend payment success callbacks is risky. | Implemented **Server-side Signature Verification** using HMAC-SHA256. |

---

## 4. Why this Tech Stack?

- **Django**: "Batteries-included" (Admin, Auth, ORM) allowed focusing on business logic: ideal for complex enterprise apps.
- **MySQL**: Relational data integrity is critical for financial transactions (Insurance).
- **Razorpay**: Developer-friendly API and excellent Sandbox support for Indian context.
- **Bootstrap 5**: Quick, responsive UI development without deep CSS expertise.
