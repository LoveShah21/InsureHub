# Key Design Decisions

## 1. Configuration-Driven Architecture

**Decision**: Instead of hardcoding premium rates (e.g., `if type == 'car': rate = 2%`), we store them in the database (`PremiumSlab` model).
**Why?**: Insurance business rules change frequently. This allows Admin users to update pricing and rules (e.g., change GST from 18% to 5%) instantly via the Panel without needing a developer to deploy code updates.

## 2. JSON for Application Data

**Decision**: Using a `JSONField` (`application_data`) in the `InsuranceApplication` model instead of creating 10 different tables for 10 insurance types.
**Why?**:
- **Flexibility**: We can launch a "Pet Insurance" product tomorrow by just defining a new schema in the frontend. The backend DB schema doesn't need migration.
- **Simplicity**: Avoids "Table Explosion" and keeps the schema clean (BCNF compliant for core fields, flexible for variable data).

## 3. Service Layer Pattern

**Decision**: extracting business logic out of `views.py` into `services.py`.
**Why?**:
- **Reusability**: The `QuoteCalculation` logic is complex. It might be needed by the Web APIs, a future Mobile App, and possibly a Batch Job. Services make this reuse possible.
- **Testing**: It's much easier to unit test a Service function than a View that requires HTTP request mocking.

## 4. Calculating Risk Scores

**Decision**: Aggregating multiple factors (Age, Medical, Driving) into a single `RiskProfile`.
**Why?**: It simplifies the Quote Engine. The engine doesn't need to know *why* a customer is high risk (smoker? bad driver?), it just needs the `risk_adjustment_percentage`. This separation of concerns makes the system modular.

## 5. Stateless JWT Authentication

**Decision**: Using JWT instead of Session Cookies for API.
**Why?**: Scalability and Mobile-readiness. If we build a React Native app later, JWT works natively. It also allows the backend to be stateless, easier to scale horizontally.
