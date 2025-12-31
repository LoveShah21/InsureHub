# Payment Integration (Razorpay)

## Overview

The system processes premium payments using **Razorpay**. We utilize the standardized "Standard Checkout" flow (Web Integration) and handle verification server-side for maximum security.

---

## 1. Integration Architecture

- **Mode**: Sandbox (Test Mode)
- **Flow**: Orders API + Checkout.js + Server-side Verification
- **Currency**: INR

### Components
1. **Frontend**: `checkout.js` script to render the payment modal.
2. **Backend Service**: `RazorpayGateway` in `apps/policies/payment_gateway.py`.
3. **Database**: `Payment` model to track transaction states.

---

## 2. Detailed Workflow

### Step 1: Order Creation (Server-Side)
Before showing the payment form, we must register the intent with Razorpay.

**API**: `POST https://api.razorpay.com/v1/orders`
**Payload**:
```json
{
  "amount": 2950000,  // Amount in paise (₹29,500)
  "currency": "INR",
  "receipt": "QT-2025-001",
  "payment_capture": 1
}
```
**Response**: Returns an `order_id` (e.g., `order_EKwx...`). We save this in our `Payment` table with status `PENDING`.

### Step 2: Checkout (Client-Side)
We pass the `order_id` to the frontend template. The user clicks "Pay" and sees the Razorpay modal.

```javascript
var options = {
    "key": "rzp_test_...",
    "amount": "2950000",
    "currency": "INR",
    "order_id": "{{ order_id }}", // From Step 1
    "handler": function (response){
        // Step 3: Send proof to backend
        verifyPayment(response);
    }
};
var rzp1 = new Razorpay(options);
rzp1.open();
```

### Step 3: Verification (Server-Side)
The frontend POSTs the response to our `/api/payments/verify/` endpoint.

**Crucial Logic**:
We do NOT trust the success message. We verify the cryptographic signature.

`HMAC_SHA256(order_id + "|" + payment_id, secret_key) == received_signature`

- **Success**: Update Payment to `SUCCESS`, Trigger Policy Issuance.
- **Failure**: Log suspicious activity, Update Payment to `FAILED`.

---

## 3. Handling Edge Cases

### Network Failures
If the internet drops after deduction but before the callback reaches our server:
- **Webhook**: We have configured a Razorpay Webhook (`payment.captured`) as a backup listener. It receives the success event asynchronously and updates the DB if the direct callback failed.

### Refunds
Refunds are currently processed manually in the Razorpay Dashboard. The system supports a `mark_refunded` admin action to update the local database status to `REFUNDED`.

---

## 4. Testing Credentials

For the Viva/Demo, use these Test Card details:

- **Card Number**: `4111 1111 1111 1111` (Visa Test)
- **Expiry**: Any future date
- **CVV**: Any 3 digits
- **OTP**: Enter any string (Simulated bank page)
