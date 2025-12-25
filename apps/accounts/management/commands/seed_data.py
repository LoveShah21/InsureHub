"""
Management command to seed the database with test data.

Usage:
    python manage.py seed_data

This creates:
- Roles and permissions
- Admin, Backoffice, and Customer users
- Insurance types and companies
- Coverage types and add-ons
- Sample applications, quotes, and policies
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal
import random

from apps.accounts.models import User, Role, Permission, UserRole
from apps.catalog.models import InsuranceType, InsuranceCompany, CoverageType, RiderAddon
from apps.customers.models import CustomerProfile
from apps.applications.models import InsuranceApplication
from apps.quotes.models import Quote
from apps.policies.models import Policy, Payment, Invoice


class Command(BaseCommand):
    help = 'Seed database with test data for development'

    def handle(self, *args, **options):
        self.stdout.write('Seeding database...\n')
        
        self.create_roles()
        self.create_permissions()
        self.create_users()
        self.create_insurance_types()
        self.create_insurance_companies()
        self.create_coverages_and_addons()
        self.create_sample_customers()
        self.create_sample_applications()
        self.create_sample_quotes()
        self.create_sample_policies()
        
        self.stdout.write(self.style.SUCCESS('\nDatabase seeding complete!'))

    def create_roles(self):
        """Create system roles."""
        self.stdout.write('Creating roles...')
        
        roles = [
            {'role_name': 'ADMIN', 'role_description': 'System Administrator', 'is_system_role': True},
            {'role_name': 'BACKOFFICE', 'role_description': 'Backoffice Staff', 'is_system_role': True},
            {'role_name': 'CUSTOMER', 'role_description': 'Customer', 'is_system_role': True},
        ]
        
        created = 0
        for role_data in roles:
            role, is_new = Role.objects.get_or_create(
                role_name=role_data['role_name'],
                defaults=role_data
            )
            if is_new:
                created += 1
        
        self.stdout.write(f'  {created} new roles created')

    def create_permissions(self):
        """Create system permissions."""
        self.stdout.write('Creating permissions...')
        
        permissions = [
            {'permission_code': 'manage_users', 'permission_description': 'Manage system users', 'resource_name': 'USER', 'action_name': 'MANAGE'},
            {'permission_code': 'manage_roles', 'permission_description': 'Manage roles', 'resource_name': 'ROLE', 'action_name': 'MANAGE'},
            {'permission_code': 'manage_catalog', 'permission_description': 'Manage insurance catalog', 'resource_name': 'CATALOG', 'action_name': 'MANAGE'},
            {'permission_code': 'view_all_policies', 'permission_description': 'View all policies', 'resource_name': 'POLICY', 'action_name': 'READ'},
            {'permission_code': 'process_applications', 'permission_description': 'Process applications', 'resource_name': 'APPLICATION', 'action_name': 'UPDATE'},
            {'permission_code': 'process_claims', 'permission_description': 'Process claims', 'resource_name': 'CLAIM', 'action_name': 'UPDATE'},
            {'permission_code': 'view_analytics', 'permission_description': 'View analytics', 'resource_name': 'ANALYTICS', 'action_name': 'READ'},
        ]
        
        created = 0
        for perm_data in permissions:
            perm, is_new = Permission.objects.get_or_create(
                permission_code=perm_data['permission_code'],
                defaults=perm_data
            )
            if is_new:
                created += 1
        
        self.stdout.write(f'  {created} new permissions created')

    def create_users(self):
        """Create admin, backoffice, and test customer users."""
        self.stdout.write('Creating users...')
        
        # Admin user
        admin_email = 'admin@insurance.local'
        if not User.objects.filter(email=admin_email).exists():
            admin = User.objects.create_superuser(
                username=admin_email,
                email=admin_email,
                password='Admin@12345',
                first_name='System',
                last_name='Admin'
            )
            admin_role = Role.objects.get(role_name='ADMIN')
            UserRole.objects.get_or_create(user=admin, role=admin_role)
            self.stdout.write(f'  Created admin: {admin_email}')
        else:
            self.stdout.write(f'  Admin already exists: {admin_email}')
        
        # Backoffice user
        backoffice_email = 'backoffice@insurance.local'
        if not User.objects.filter(email=backoffice_email).exists():
            backoffice = User.objects.create_user(
                username=backoffice_email,
                email=backoffice_email,
                password='Backoffice@123',
                first_name='Back',
                last_name='Office'
            )
            backoffice_role = Role.objects.get(role_name='BACKOFFICE')
            UserRole.objects.get_or_create(user=backoffice, role=backoffice_role)
            self.stdout.write(f'  Created backoffice: {backoffice_email}')
        else:
            self.stdout.write(f'  Backoffice already exists: {backoffice_email}')
        
        # Test customer
        customer_email = 'customer@test.com'
        if not User.objects.filter(email=customer_email).exists():
            customer = User.objects.create_user(
                username=customer_email,
                email=customer_email,
                password='Customer@123',
                first_name='Test',
                last_name='Customer'
            )
            customer_role = Role.objects.get(role_name='CUSTOMER')
            UserRole.objects.get_or_create(user=customer, role=customer_role)
            
            # Create customer profile (using correct field names from CustomerProfile model)
            CustomerProfile.objects.get_or_create(
                user=customer,
                defaults={
                    'date_of_birth': date(1990, 5, 15),
                    'gender': 'MALE',
                    'residential_address': '123 Test Street',
                    'residential_city': 'Mumbai',
                    'residential_state': 'Maharashtra',
                    'residential_pincode': '400001',
                    'occupation_type': 'SALARIED',
                    'annual_income': Decimal('1200000.00'),
                }
            )
            self.stdout.write(f'  Created customer: {customer_email}')
        else:
            self.stdout.write(f'  Customer already exists: {customer_email}')

    def create_insurance_types(self):
        """Create insurance types."""
        self.stdout.write('Creating insurance types...')
        
        # InsuranceType fields: type_name, type_code, description, is_active
        types = [
            {
                'type_name': 'Motor Insurance',
                'type_code': 'MOTOR',
                'description': 'Comprehensive motor vehicle insurance covering accidents, theft, and third-party liability.',
            },
            {
                'type_name': 'Health Insurance',
                'type_code': 'HEALTH',
                'description': 'Medical insurance covering hospitalization, surgeries, and medical expenses.',
            },
            {
                'type_name': 'Term Life Insurance',
                'type_code': 'TERM_LIFE',
                'description': 'Pure life insurance providing financial protection to beneficiaries.',
            },
            {
                'type_name': 'Travel Insurance',
                'type_code': 'TRAVEL',
                'description': 'Coverage for travel-related risks including trip cancellation and medical emergencies.',
            },
            {
                'type_name': 'Home Insurance',
                'type_code': 'HOME',
                'description': 'Protection for your home and contents against damage and theft.',
            },
        ]
        
        created = 0
        for type_data in types:
            obj, is_new = InsuranceType.objects.get_or_create(
                type_code=type_data['type_code'],
                defaults=type_data
            )
            if is_new:
                created += 1
        
        self.stdout.write(f'  {created} new insurance types created')

    def create_insurance_companies(self):
        """Create insurance companies."""
        self.stdout.write('Creating insurance companies...')
        
        # InsuranceCompany fields: company_name, company_code, registration_number, headquarters_address,
        # contact_email, contact_phone, website, logo_url, claim_settlement_ratio (0-1), service_rating (0-5)
        companies = [
            {
                'company_name': 'LIC of India',
                'company_code': 'LIC',
                'headquarters_address': 'Mumbai, Maharashtra',
                'website': 'https://licindia.in',
                'contact_phone': '1800-258-9999',
                'claim_settlement_ratio': Decimal('0.985'),
                'service_rating': Decimal('4.5'),
            },
            {
                'company_name': 'HDFC Life',
                'company_code': 'HDFC_LIFE',
                'headquarters_address': 'Mumbai, Maharashtra',
                'website': 'https://hdfclife.com',
                'contact_phone': '1800-266-9777',
                'claim_settlement_ratio': Decimal('0.978'),
                'service_rating': Decimal('4.3'),
            },
            {
                'company_name': 'ICICI Lombard',
                'company_code': 'ICICI_LOMBARD',
                'headquarters_address': 'Mumbai, Maharashtra',
                'website': 'https://icicilombard.com',
                'contact_phone': '1800-266-2266',
                'claim_settlement_ratio': Decimal('0.965'),
                'service_rating': Decimal('4.2'),
            },
            {
                'company_name': 'Bajaj Allianz',
                'company_code': 'BAJAJ_ALLIANZ',
                'headquarters_address': 'Pune, Maharashtra',
                'website': 'https://bajajallianz.com',
                'contact_phone': '1800-209-5858',
                'claim_settlement_ratio': Decimal('0.950'),
                'service_rating': Decimal('4.0'),
            },
            {
                'company_name': 'Tata AIG',
                'company_code': 'TATA_AIG',
                'headquarters_address': 'Mumbai, Maharashtra',
                'website': 'https://tataaig.com',
                'contact_phone': '1800-266-7780',
                'claim_settlement_ratio': Decimal('0.945'),
                'service_rating': Decimal('3.9'),
            },
        ]
        
        created = 0
        for company_data in companies:
            obj, is_new = InsuranceCompany.objects.get_or_create(
                company_code=company_data['company_code'],
                defaults=company_data
            )
            if is_new:
                created += 1
        
        self.stdout.write(f'  {created} new insurance companies created')

    def create_coverages_and_addons(self):
        """Create coverage types and rider add-ons."""
        self.stdout.write('Creating coverages and add-ons...')
        
        motor = InsuranceType.objects.filter(type_code='MOTOR').first()
        health = InsuranceType.objects.filter(type_code='HEALTH').first()
        
        coverages_created = 0
        addons_created = 0
        
        if motor:
            # CoverageType fields: coverage_name, coverage_code, insurance_type, description, 
            # is_mandatory, base_premium_per_unit, unit_of_measurement
            motor_coverages = [
                {'coverage_name': 'Third Party Liability', 'coverage_code': 'TPL', 'is_mandatory': True, 'base_premium_per_unit': Decimal('1000')},
                {'coverage_name': 'Own Damage', 'coverage_code': 'OD', 'is_mandatory': False, 'base_premium_per_unit': Decimal('2500')},
                {'coverage_name': 'Personal Accident', 'coverage_code': 'PA', 'is_mandatory': True, 'base_premium_per_unit': Decimal('500')},
            ]
            for cov in motor_coverages:
                obj, is_new = CoverageType.objects.get_or_create(
                    insurance_type=motor,
                    coverage_code=cov['coverage_code'],
                    defaults={**cov, 'insurance_type': motor}
                )
                if is_new:
                    coverages_created += 1
            
            # RiderAddon fields: addon_name, addon_code, insurance_type, description,
            # premium_percentage, is_optional, max_coverage_limit
            motor_addons = [
                {'addon_name': 'Zero Depreciation', 'addon_code': 'ZERO_DEP', 'premium_percentage': Decimal('15.00')},
                {'addon_name': 'Roadside Assistance', 'addon_code': 'RSA', 'premium_percentage': Decimal('5.00')},
                {'addon_name': 'Engine Protection', 'addon_code': 'ENGINE', 'premium_percentage': Decimal('10.00')},
            ]
            for addon in motor_addons:
                obj, is_new = RiderAddon.objects.get_or_create(
                    insurance_type=motor,
                    addon_code=addon['addon_code'],
                    defaults={**addon, 'insurance_type': motor}
                )
                if is_new:
                    addons_created += 1
        
        if health:
            health_coverages = [
                {'coverage_name': 'Hospitalization', 'coverage_code': 'HOSP', 'is_mandatory': True, 'base_premium_per_unit': Decimal('5000')},
                {'coverage_name': 'Pre-Hospitalization', 'coverage_code': 'PRE_HOSP', 'is_mandatory': False, 'base_premium_per_unit': Decimal('1000')},
                {'coverage_name': 'Post-Hospitalization', 'coverage_code': 'POST_HOSP', 'is_mandatory': False, 'base_premium_per_unit': Decimal('1000')},
            ]
            for cov in health_coverages:
                obj, is_new = CoverageType.objects.get_or_create(
                    insurance_type=health,
                    coverage_code=cov['coverage_code'],
                    defaults={**cov, 'insurance_type': health}
                )
                if is_new:
                    coverages_created += 1
            
            health_addons = [
                {'addon_name': 'Critical Illness', 'addon_code': 'CI', 'premium_percentage': Decimal('20.00')},
                {'addon_name': 'Maternity Cover', 'addon_code': 'MATERNITY', 'premium_percentage': Decimal('25.00')},
            ]
            for addon in health_addons:
                obj, is_new = RiderAddon.objects.get_or_create(
                    insurance_type=health,
                    addon_code=addon['addon_code'],
                    defaults={**addon, 'insurance_type': health}
                )
                if is_new:
                    addons_created += 1
        
        self.stdout.write(f'  {coverages_created} coverages, {addons_created} add-ons created')

    def create_sample_customers(self):
        """Create additional sample customers."""
        self.stdout.write('Creating sample customers...')
        
        customers = [
            {
                'email': 'john.doe@example.com',
                'first_name': 'John',
                'last_name': 'Doe',
                'dob': date(1985, 3, 20),
                'gender': 'MALE',
                'income': Decimal('1500000'),
            },
            {
                'email': 'jane.smith@example.com',
                'first_name': 'Jane',
                'last_name': 'Smith',
                'dob': date(1992, 8, 10),
                'gender': 'FEMALE',
                'income': Decimal('900000'),
            },
        ]
        
        customer_role = Role.objects.get(role_name='CUSTOMER')
        created = 0
        
        for cust_data in customers:
            if not User.objects.filter(email=cust_data['email']).exists():
                user = User.objects.create_user(
                    username=cust_data['email'],
                    email=cust_data['email'],
                    password='Customer@123',
                    first_name=cust_data['first_name'],
                    last_name=cust_data['last_name']
                )
                UserRole.objects.get_or_create(user=user, role=customer_role)
                CustomerProfile.objects.create(
                    user=user,
                    date_of_birth=cust_data['dob'],
                    gender=cust_data['gender'],
                    residential_address=f'{random.randint(1,999)} Sample Street',
                    residential_city='Mumbai',
                    residential_state='Maharashtra',
                    residential_pincode='400001',
                    occupation_type='PROFESSIONAL',
                    annual_income=cust_data['income'],
                )
                created += 1
        
        self.stdout.write(f'  {created} new sample customers created')

    def create_sample_applications(self):
        """Create sample insurance applications."""
        self.stdout.write('Creating sample applications...')
        
        customer_profiles = CustomerProfile.objects.all()[:3]
        motor = InsuranceType.objects.filter(type_code='MOTOR').first()
        health = InsuranceType.objects.filter(type_code='HEALTH').first()
        
        if not customer_profiles or not motor:
            self.stdout.write('  Skipping - no customers or insurance types')
            return
        
        created = 0
        for i, profile in enumerate(customer_profiles):
            ins_type = motor if i % 2 == 0 else health
            if ins_type:
                # InsuranceApplication fields: customer, insurance_type, status, application_data,
                # requested_coverage_amount, policy_tenure_months, budget_min, budget_max
                app, is_new = InsuranceApplication.objects.get_or_create(
                    customer=profile,
                    insurance_type=ins_type,
                    status='APPROVED',
                    defaults={
                        'requested_coverage_amount': Decimal('500000') if ins_type == motor else Decimal('1000000'),
                        'policy_tenure_months': 12,
                        'application_data': {'vehicle_type': 'Car'} if ins_type == motor else {'family_size': 4},
                        'submission_date': timezone.now(),
                        'approval_date': timezone.now(),
                    }
                )
                if is_new:
                    created += 1
        
        self.stdout.write(f'  {created} new applications created')

    def create_sample_quotes(self):
        """Create sample quotes for approved applications."""
        self.stdout.write('Creating sample quotes...')
        
        applications = InsuranceApplication.objects.filter(status='APPROVED')
        companies = list(InsuranceCompany.objects.all()[:3])
        
        if not applications or not companies:
            self.stdout.write('  Skipping - no applications or companies')
            return
        
        created = 0
        for app in applications:
            for company in companies:
                # Check if quote already exists
                if Quote.objects.filter(application=app, insurance_company=company).exists():
                    continue
                
                # Quote fields: quote_number, application, customer, insurance_type, insurance_company,
                # status, base_premium, risk_adjustment_percentage, adjusted_premium,
                # fleet_discount_percentage, fleet_discount_amount, loyalty_discount_percentage,
                # loyalty_discount_amount, other_discounts_amount, final_premium, gst_percentage,
                # gst_amount, total_premium_with_gst, sum_insured, policy_tenure_months,
                # validity_days, expiry_at, overall_score
                
                coverage_amount = app.requested_coverage_amount or Decimal('500000')
                base_premium = coverage_amount * Decimal('0.025')
                adjusted_premium = base_premium
                final_premium = adjusted_premium
                gst = final_premium * Decimal('0.18')
                
                quote = Quote.objects.create(
                    application=app,
                    customer=app.customer,
                    insurance_type=app.insurance_type,
                    insurance_company=company,
                    status='GENERATED',
                    base_premium=base_premium,
                    adjusted_premium=adjusted_premium,
                    final_premium=final_premium,
                    gst_percentage=Decimal('18.0'),
                    gst_amount=gst,
                    total_premium_with_gst=final_premium + gst,
                    sum_insured=coverage_amount,
                    policy_tenure_months=app.policy_tenure_months,
                    validity_days=30,
                    expiry_at=timezone.now() + timedelta(days=30),
                    overall_score=Decimal(str(random.randint(70, 95))),
                )
                created += 1
        
        self.stdout.write(f'  {created} new quotes created')

    def create_sample_policies(self):
        """Create a sample active policy."""
        self.stdout.write('Creating sample policies...')
        
        # Get first quote and mark it accepted
        quote = Quote.objects.filter(status='GENERATED').first()
        if not quote:
            self.stdout.write('  Skipping - no quotes available')
            return
        
        if Policy.objects.filter(quote=quote).exists():
            self.stdout.write('  Sample policy already exists')
            return
        
        quote.status = 'ACCEPTED'
        quote.accepted_at = timezone.now()
        quote.save()
        
        start_date = date.today() - timedelta(days=30)
        end_date = start_date + timedelta(days=365)
        
        policy = Policy.objects.create(
            quote=quote,
            customer=quote.customer,
            insurance_type=quote.insurance_type,
            insurance_company=quote.insurance_company,
            status='ACTIVE',
            policy_start_date=start_date,
            policy_end_date=end_date,
            policy_tenure_months=12,
            premium_amount=quote.final_premium,
            gst_amount=quote.gst_amount,
            total_premium_with_gst=quote.total_premium_with_gst,
            sum_insured=quote.sum_insured,
            issued_at=timezone.now(),
            next_renewal_date=end_date,
        )
        
        # Create payment record
        payment = Payment.objects.create(
            quote=quote,
            policy=policy,
            customer=quote.customer,
            payment_amount=quote.total_premium_with_gst,
            payment_method='RAZORPAY',
            status='SUCCESS',
            razorpay_order_id=f'order_test_{policy.policy_number[-8:]}',
            razorpay_payment_id=f'pay_test_{policy.policy_number[-8:]}',
            payment_date=timezone.now(),
        )
        
        # Create invoice
        Invoice.objects.create(
            policy=policy,
            payment=payment,
            invoice_date=date.today(),
            invoice_amount=quote.final_premium,
            gst_amount=quote.gst_amount,
            total_invoice_amount=quote.total_premium_with_gst,
            status='PAID',
        )
        
        self.stdout.write(f'  Created policy: {policy.policy_number}')
