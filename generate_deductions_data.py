import os
import django
import random
from datetime import datetime, timedelta
from decimal import Decimal

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'deductions360.settings')
django.setup()

from osd.models import Deductions

# List of sample customers (keeping your actual customers if possible)
CUSTOMERS = [
    'Walmart', 'Target', 'Costco', 'Kroger', 'Albertsons',
    'Safeway', 'Whole Foods', 'Sam\'s Club', 'Publix', 'Aldi'
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

def generate_test_data(num_records=500, delete_existing=True):
    if delete_existing:
        confirm = input("Are you sure you want to delete existing data? (yes/no): ")
        if confirm.lower() == 'yes':
            Deductions.objects.all().delete()
            print("Existing data deleted.")
        else:
            print("Keeping existing data.")    # Get the latest existing date or use default if no records exist
    latest_date = Deductions.objects.order_by('-deduction_date').values_list('deduction_date', flat=True).first()
    start_date = datetime.combine(latest_date + timedelta(days=1), datetime.min.time()) if latest_date else datetime(2023, 1, 1)
    end_date = start_date + timedelta(days=30)  # Generate data for the next 30 days
    
    print(f"Generating data from {start_date.date()} to {end_date.date()}")
    
    for i in range(num_records):
        deduction_date = generate_random_date(start_date, end_date)
        deducted_amount = Decimal(str(random.uniform(100.0, 10000.0))).quantize(Decimal('0.01'))
        
        # Calculate valid and invalid amounts
        valid_percentage = random.uniform(0.3, 0.8)  # 30-80% valid
        valid_amount = (deducted_amount * Decimal(str(valid_percentage))).quantize(Decimal('0.01'))
        invalid_amount = (deducted_amount - valid_amount).quantize(Decimal('0.01'))
        
        # Create deduction record
        deduction = Deductions.objects.create(
            deduction_reference=f'DR{i+1:06d}',
            standard_customer=random.choice(CUSTOMERS),
            invoice_number=f'91{random.randint(10000000, 99999999)}',
            deducted_amount=deducted_amount,
            deduction_date=deduction_date,
            deduction_reason=random.choice(REASONS),
            validation_status=random.choice(['Valid', 'Invalid', 'Pending']),
            valid_amount=valid_amount,
            invalid_amount=invalid_amount,            status=random.choice(['Pending Validation', 'Validated', 'Billed Back', 'Recovered']),
            date_worked=deduction_date + timedelta(days=random.randint(1, 30)),
            tolerance='UT' if deducted_amount < Decimal('500.00') else 'OT'
        )
        
        print(f'Created record {i+1}: {deduction.deduction_reference} - ${deduction.deducted_amount}')

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate test data for Deductions model')
    parser.add_argument('--records', type=int, default=100, help='Number of records to generate')
    parser.add_argument('--delete', action='store_true', help='Delete existing data before generating new records')
    
    args = parser.parse_args()
    
    print(f'Generating {args.records} test records...')
    generate_test_data(args.records, args.delete)
    print('Test data generation complete!')
