# Testing Strategy

## Overview

A robust application requires a comprehensive testing strategy. For this project, we employ a "Texting Pyramid" approach comprising Unit Tests (base), Integration Tests (middle), and Manual/UAT Tests (top).

---

## 1. Automated Testing (Django)

We use Django's built-in `TestCase` framework.

### Unit Tests
Focus on testing individual functions and models in isolation.

**Key Areas:**
- **Model Methods**:
  - Test `User.failed_login_attempts` increments correctly.
  - Test `Quote.calculate_tax()` returns 18% of premium.
- **Service Logic**:
  - Test `QuoteService` premium calculation with boundary values (`min`, `max` sum insured).
  - Test `ClaimsWorkflowService` allows valid transitions and blocks invalid ones.

**Example Test:**
```python
def test_premium_calculation(self):
    quote = QuoteService.generate(sum_insured=500000)
    self.assertEqual(quote.base_premium, 12500)
```

### Integration Tests
Focus on testing the interaction between modules.

**Key Scenarios:**
- **Application → Quote**: Create application, approve it, ensure quote can be generated.
- **Quote → Policy**: Accept quote, trigger payment signal, verify Policy is created.
- **API Tests**: Send POST request to `/api/claims/submit/` and verify DB record is created.

---

## 2. Manual Testing (UAT)

Since this is a UI-heavy application, manual testing is critical.

### Role-Based Checklists

**Admin:**
- [ ] Create a new Insurance Type ("Pet Insurance").
- [ ] Update GST Configuration.
- [ ] Create a Backoffice user.

**Backoffice:**
- [ ] View submitted applications.
- [ ] Generate a quote (Verify math).
- [ ] Approve a claim < Threshold.
- [ ] Attempt to approve claim > Threshold (Verify error).

**Customer:**
- [ ] Registration & Login.
- [ ] Profile Completion.
- [ ] Submit Application (Upload dummy docs).
- [ ] View Quote.
- [ ] Dummy Payment (Razorpay Success).
- [ ] Download Policy.

---

## 3. Security Testing

- **SQL Injection**: Attempt to pass `' OR 1=1 --` in login fields.
- **XSS**: Attempt to enter `<script>alert(1)</script>` in claim description.
- **Authorization**: Try to access `/panel/` URL while logged in as Customer (Expect 403/Redirect).

---

## 4. Test Data Generation

A `seed_data` command is provided to populate the database for testing/demo:
```bash
python manage.py seed_data
```
This creates:
- 1 Admin User (`admin@example.com`)
- 1 Backoffice User
- 2 Customers with Profiles
- 3 Insurance Types
- Dummy Policies and Claims
