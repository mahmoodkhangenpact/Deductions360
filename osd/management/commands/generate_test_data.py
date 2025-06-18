from django.core.management.base import BaseCommand
from django.utils import timezone
from osd.models import Deductions
import random
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Generates test data for deductions'

    def handle(self, *args, **kwargs):
        # Clear existing deductions
        Deductions.objects.all().delete()

        # Generate data for last 4 quarters
        customers = ['Customer A', 'Customer B', 'Customer C']
        deduction_reasons = ['Pricing', 'Shortage', 'Damage', 'Returns']
        status_choices = ['Pending Validation', 'Validated', 'Billed Back', 'Recovered']
        validation_status_choices = ['Valid', 'Invalid', 'Pending']

        current_date = timezone.now()
        
        # Generate deductions for the last 4 quarters
        for i in range(400):  # Generate 400 deductions
            # Random date in last 12 months
            days_back = random.randint(0, 365)
            deduction_date = current_date - timedelta(days=days_back)
            
            # Determine validation status (weighted towards pending)
            validation_status = random.choices(
                validation_status_choices, 
                weights=[0.2, 0.3, 0.5]  # 20% Valid, 30% Invalid, 50% Pending
            )[0]

            # Set amounts based on validation status
            deducted_amount = random.randint(1000, 50000)
            valid_amount = deducted_amount if validation_status == 'Valid' else 0
            invalid_amount = deducted_amount if validation_status == 'Invalid' else 0

            # Create deduction
            deduction = Deductions.objects.create(
                deduction_reference=f'TEST-{i+1}',
                standard_customer=random.choice(customers),
                invoice_number=f'INV-{random.randint(10000, 99999)}',
                deducted_amount=deducted_amount,
                deduction_date=deduction_date,
                deduction_reason=random.choice(deduction_reasons),
                status=random.choice(status_choices),
                validation_status=validation_status,
                valid_amount=valid_amount,
                invalid_amount=invalid_amount,
                date_worked=deduction_date if random.random() > 0.3 else None  # 70% chance of having date_worked
            )

            # Set open/closed status
            deduction.open_closed = 'Closed' if validation_status == 'Invalid' else 'Open'
            deduction.save()

        self.stdout.write(self.style.SUCCESS('Successfully generated test data'))
