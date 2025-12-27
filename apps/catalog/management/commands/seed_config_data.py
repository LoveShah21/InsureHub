"""
Seed Config Data Command

Creates sample configuration data for:
- PremiumSlab
- PolicyEligibilityRule  
- DiscountRule
- BusinessConfiguration

Usage: python manage.py seed_config_data
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal

from apps.catalog.models import InsuranceType
from apps.catalog.config_models import (
    PremiumSlab,
    PolicyEligibilityRule,
    DiscountRule,
    BusinessConfiguration,
)


class Command(BaseCommand):
    help = 'Seed configuration data for config models'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write('Seeding configuration data...\n')
        
        # Get insurance types
        insurance_types = list(InsuranceType.objects.all())
        if not insurance_types:
            self.stdout.write(self.style.ERROR('No insurance types found. Run seed_data first.'))
            return
        
        # Seed Premium Slabs
        self._seed_premium_slabs(insurance_types)
        
        # Seed Eligibility Rules
        self._seed_eligibility_rules(insurance_types)
        
        # Seed Discount Rules
        self._seed_discount_rules()
        
        # Seed Business Configuration
        self._seed_business_config()
        
        self.stdout.write(self.style.SUCCESS('\nConfiguration data seeded successfully!'))
    
    def _seed_premium_slabs(self, insurance_types):
        """Create premium slabs for each insurance type."""
        self.stdout.write('Creating Premium Slabs...')
        
        slabs_data = [
            # (min, max, base_premium, markup%)
            (0, 100000, 1000, Decimal('1.5')),
            (100001, 500000, 2500, Decimal('1.2')),
            (500001, 1000000, 5000, Decimal('1.0')),
            (1000001, 5000000, 10000, Decimal('0.8')),
            (5000001, 10000000, 25000, Decimal('0.6')),
        ]
        
        count = 0
        for ins_type in insurance_types:
            for i, (min_cov, max_cov, base, markup) in enumerate(slabs_data):
                slab, created = PremiumSlab.objects.get_or_create(
                    insurance_type=ins_type,
                    min_coverage_amount=min_cov,
                    max_coverage_amount=max_cov,
                    defaults={
                        'slab_name': f'{ins_type.type_code} Slab {i+1}',
                        'base_premium': Decimal(str(base)),
                        'percentage_markup': markup,
                        'is_active': True
                    }
                )
                if created:
                    count += 1
        
        self.stdout.write(f'  Created {count} premium slabs')
    
    def _seed_eligibility_rules(self, insurance_types):
        """Create eligibility rules for insurance types."""
        self.stdout.write('Creating Eligibility Rules...')
        
        rules_data = {
            'HEALTH': [
                ('Age Requirement', {'min_age': 18, 'max_age': 65}, 1, 'Applicant must be between 18 and 65 years old'),
            ],
            'MOTOR': [
                ('Valid License', {'has_valid_license': True}, 1, 'Applicant must have a valid driving license'),
                ('Vehicle Age', {'max_vehicle_age': 15}, 2, 'Vehicle must be less than 15 years old'),
            ],
            'LIFE': [
                ('Age Requirement', {'min_age': 18, 'max_age': 60}, 1, 'Applicant must be between 18 and 60 years old'),
            ],
            'HOME': [
                ('Property Age', {'max_property_age': 50}, 1, 'Property must be less than 50 years old'),
            ],
            'TRAVEL': [
                ('Age Requirement', {'min_age': 0, 'max_age': 70}, 1, 'Traveler must be under 70 years old'),
            ],
        }
        
        count = 0
        for ins_type in insurance_types:
            type_code = ins_type.type_code
            if type_code in rules_data:
                for rule_name, condition, priority, error_msg in rules_data[type_code]:
                    rule, created = PolicyEligibilityRule.objects.get_or_create(
                        insurance_type=ins_type,
                        rule_name=rule_name,
                        defaults={
                            'rule_condition': condition,  # Singular!
                            'rule_priority': priority,
                            'error_message': error_msg,
                            'is_active': True
                        }
                    )
                    if created:
                        count += 1
        
        self.stdout.write(f'  Created {count} eligibility rules')
    
    def _seed_discount_rules(self):
        """Create discount rules."""
        self.stdout.write('Creating Discount Rules...')
        
        discounts = [
            # (name, code, percentage, conditions, priority)
            ('Early Bird Discount', 'EARLY_BIRD', Decimal('5.0'), {'days_before_expiry': 30}, 1),
            ('No Claim Bonus', 'NO_CLAIM', Decimal('10.0'), {'claim_free_years': 1}, 2),
            ('Multi-Policy Discount', 'MULTI_POLICY', Decimal('7.5'), {'min_policies': 2}, 3),
            ('Fleet Discount Small', 'FLEET_SMALL', Decimal('5.0'), {'min_fleet_size': 5}, 4),
            ('Fleet Discount Medium', 'FLEET_MED', Decimal('10.0'), {'min_fleet_size': 10}, 5),
            ('Fleet Discount Large', 'FLEET_LARGE', Decimal('15.0'), {'min_fleet_size': 20}, 6),
            ('Senior Citizen Discount', 'SENIOR', Decimal('3.0'), {'min_age': 60}, 7),
            ('Women Driver Discount', 'WOMEN_DRV', Decimal('5.0'), {'gender': 'F'}, 8),
        ]
        
        count = 0
        for name, code, percentage, condition, priority in discounts:
            discount, created = DiscountRule.objects.get_or_create(
                rule_code=code,  # Unique identifier
                defaults={
                    'rule_name': name,
                    'discount_percentage': percentage,
                    'rule_condition': condition,  # Singular!
                    'rule_priority': priority,
                    'is_active': True,
                    'is_combinable': True
                }
            )
            if created:
                count += 1
        
        self.stdout.write(f'  Created {count} discount rules')
    
    def _seed_business_config(self):
        """Create business configuration settings."""
        self.stdout.write('Creating Business Configuration...')
        
        configs = [
            ('GST_RATE', '18', 'TAX', 'GST percentage applied to premiums'),
            ('DEFAULT_POLICY_TENURE', '12', 'GENERAL', 'Default policy tenure in months'),
            ('MAX_POLICY_TENURE', '36', 'GENERAL', 'Maximum policy tenure in months'),
            ('QUOTE_VALIDITY_DAYS', '30', 'QUOTE', 'Number of days a quote is valid'),
            ('MAX_QUOTES_PER_APPLICATION', '5', 'QUOTE', 'Maximum quotes per application'),
            ('CLAIM_SUBMISSION_DEADLINE', '30', 'CLAIM', 'Days within which claim must be filed'),
            ('AUTO_APPROVE_THRESHOLD', '10000', 'CLAIM', 'Claims below this amount auto-approve'),
            ('RENEWAL_REMINDER_DAYS', '30', 'GENERAL', 'Days before expiry to send reminder'),
            ('PAYMENT_GATEWAY', 'RAZORPAY', 'PAYMENT', 'Active payment gateway'),
            ('CURRENCY_CODE', 'INR', 'GENERAL', 'Currency code for transactions'),
        ]
        
        count = 0
        for key, value, config_type, desc in configs:
            config, created = BusinessConfiguration.objects.get_or_create(
                config_key=key,
                defaults={
                    'config_value': value,
                    'config_type': config_type,
                    'config_description': desc,  # Correct field name
                    'is_active': True
                }
            )
            if created:
                count += 1
        
        self.stdout.write(f'  Created {count} business configurations')
