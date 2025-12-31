# System Flow Summaries available

## 1. The "Application to Policy" Journey

1.  **User Actions**: User registers, completes profile, selects "Motor Insurance", fills vehicle details (`application_data`), and submits.
2.  **Backoffice**: Staff reviews uploaded documents (RC/ID). Marks application `APPROVED`.
3.  **Quote Engine**: Staff generates a quote. System calculates Base `Premium` + `Risk Loading` - `Discounts`.
4.  **Customer Choice**: Customer views quote, sees "Recommended" tag based on scoring. Clicks "Pay".
5.  **Payment**: Razorpay modal opens. User pays. Backend verifies signature.
6.  **Issuance**: System marks payment `SUCCESS`, creates `Policy` record (Active for 1 year), generates `Invoice`, and emails the user.

## 2. The "Claim to Settlement" Journey

1.  **Submission**: Customer selects Active Policy, reports accident, uploads photos.
2.  **Validation**: System checks if Policy is active and incident date is within coverage period.
3.  **Review**: Backoffice verifies photos.
4.  **Approval Logic**: Officer attempts to approve ₹50,000. System checks `ClaimApprovalThreshold`. If user has `limit >= 50,000`, approved. Else, error.
5.  **Settlement**: Officer clicks "Process Payout". System marks claim `SETTLED`.

## 3. The "Risk Assessment" Background Process

1.  **Trigger**: User updates Profile or Medical History.
2.  **Calculation**: Service fetches Age, Medical Flags (Smoker), Driving History (Accidents).
3.  **Weighting**: Applies formula `(Age*0.2 + Medical*0.3 + ...)` to get Score (0-100).
4.  **Categorization**: Maps Score to Category (e.g., 75 -> HIGH).
5.  **Output**: Updates `CustomerRiskProfile`. Next quote generated will automatically fetch this new risk factor.
