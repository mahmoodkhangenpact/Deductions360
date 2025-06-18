import os
import django
import random
from datetime import datetime, timedelta
from decimal import Decimal

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'deductions360.settings')
django.setup()

from osd.models import workflow

# List of sample customers
CUSTOMERS = [
    'Walmart', 'Target', 'Costco', 'Kroger', 'Albertsons',
    'Safeway', 'Whole Foods', 'Sam\'s Club', 'Publix', 'Aldi'
]

# List of sample carriers
CARRIERS = [
    'FedEx', 'UPS', 'USPS', 'DHL', 'XPO Logistics',
    'J.B. Hunt', 'Schneider', 'Swift', 'Werner', 'C.H. Robinson'
]

# List of deduction reasons
REASONS = [
    'Damaged Products', 'Missing Items', 'Late Delivery',
    'Price Discrepancy', 'Quantity Mismatch', 'Quality Issues',
    'Wrong Product Shipped', 'Billing Error', 'Promotional Discount',
    'Return Processing'
]

def generate_random_date(start_date, end_date):
    time_between_dates = end_date - start_date
    days_between_dates = time_between_dates.days
    random_number_of_days = random.randrange(days_between_dates)
    return start_date + timedelta(days=random_number_of_days)

def generate_test_data(num_records=100):
    # Get the latest existing date or use default if no records exist
    latest_date = workflow.objects.order_by('-deduction_date').values_list('deduction_date', flat=True).first()
    
    start_date = latest_date + timedelta(days=1) if latest_date else datetime(2023, 1, 1)
    end_date = datetime(2025, 6, 11)  # Current date
    
    for i in range(num_records):
        deduction_date = generate_random_date(start_date, end_date)
        deducted_qty = random.randint(10, 1000)
        price_per_qty = Decimal(str(random.uniform(5.0, 100.0))).quantize(Decimal('0.01'))
        deducted_amount = Decimal(str(deducted_qty * float(price_per_qty))).quantize(Decimal('0.01'))
        
        # Calculate valid and invalid amounts
        valid_percentage = random.uniform(0.3, 0.8)  # 30-80% valid
        valid_amount = (deducted_amount * Decimal(str(valid_percentage))).quantize(Decimal('0.01'))
        invalid_amount = (deducted_amount - valid_amount).quantize(Decimal('0.01'))
        
        # Create workflow record
        w = workflow.objects.create(
            ids=f'ID{i+1:05d}',
            standard_customer=random.choice(CUSTOMERS),
            deduction_reference=f'DR{i+1:06d}',
            invoice_number=f'91{random.randint(10000000, 99999999)}',
            deducted_amount=deducted_amount,
            deducted_qty=deducted_qty,
            deducted_price_per_qty=price_per_qty,
            deduction_date=deduction_date,
            deduction_reason=random.choice(REASONS),
            billed_qty=deducted_qty + random.randint(-50, 50),
            gross_price_per_qty=price_per_qty + Decimal(str(random.uniform(0, 5))),
            net_price_per_qty=price_per_qty,
            carrier=random.choice(CARRIERS),
            shortage=random.randint(0, 50),
            damage=random.randint(0, 30),
            returns=random.randint(0, 20),
            overage=random.randint(0, 10),
            validation_status=random.choice(['Valid', 'Invalid', 'Pending']),
            valid_amount=valid_amount,
            invalid_amount=invalid_amount,
            status=random.choice(['Pending Validation', 'Validated', 'Billed Back', 'Recovered']),
            date_worked=deduction_date + timedelta(days=random.randint(1, 30))
        )
        
        print(f'Created record {i+1}: {w.deduction_reference} - ${w.deducted_amount}')

if __name__ == '__main__':
    num_records = 500  # Adjust this number to generate more or fewer records
    print(f'Generating {num_records} test records...')
    generate_test_data(num_records)
    print('Test data generation complete!')
