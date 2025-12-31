# Limitations and Future Scope

## 1. Current System Limitations

While the system is robust for a university project, certain simplifications were made:

### Technical Limitations
- **Scalability**: Synchronous processes (like email sending) can block the request thread. In production, these should be offloaded to Celery/Redis queues.
- **Database**: Currently optimized for read/write integrity but lacks read-replicas or sharding for massive scale.
- **Search**: Uses basic SQL `LIKE` queries. Full-text search (Elasticsearch) would be faster for millions of records.

### Functional Limitations
- **Payment Gateway**: Only Supports Razorpay Sandbox. Real refund processing logic is mocked.
- **KYC Verification**: Document verification is manual (human review). No integration with government APIs (like NSDL for PAN).
- **Hardcoded Rules**: While many rules are config-driven, some complex eligibility logic remains in Python services.

---

## 2. Future Scope

### Phase 1: Automation & AI
- **Automated Underwriting**: Use ML models to predict risk score automatically instead of rule-based logic.
- **Image Recognition**: Auto-verify car damage photos for claims using Computer Vision.
- **Chatbot**: AI-powered customer support bot for FAQs and status checks.

### Phase 2: Integrations
- **WhatsApp Integration**: Send policies and alerts via WhatsApp API.
- **Government APIs**: Real-time PAN/Aadhaar/DL verification.
- **Bank APIs**: Direct settlement to bank accounts (Payouts).

### Phase 3: Mobile App
- Develop a Flutter/React Native app using the existing REST APIs.
- Features: Geolocation-based roadside assistance, Photo upload for claims.

### Phase 4: Business Intelligence
- **Data Warehouse**: ETL pipeline to move data to data warehouse (Snowflake/BigQuery).
- **Advanced Reporting**: PowerBI/Tableau integration for deep actuarial analysis.
