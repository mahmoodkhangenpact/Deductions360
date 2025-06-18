import os
import django
import random
from datetime import datetime, timedelta
from decimal import Decimal

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'deductions360.settings')
django.setup()

from osd.models import Invoice, Deductions

def generate_random_invoice_number():
    return str(random.randint(9100000000, 9199999999))

def generate_random_net_amount():
    return Decimal(str(random.uniform(100, 10000))).quantize(Decimal('0.01'))

def generate_random_date(start_date, end_date):
    time_between_dates = end_date - start_date
    days_between_dates = time_between_dates.days
    random_number_of_days = random.randrange(days_between_dates)
    return start_date + timedelta(days=random_number_of_days)

def generate_random_sku():
    return f"SKU-{random.randint(1000, 9999)}"

def generate_random_order():
    return f"ORD-{random.randint(100000, 999999)}"

def generate_random_bol():
    return f"BOL-{random.randint(10000, 99999)}"

def generate_random_carrier():
    carriers = [
        "UPS", "FedEx", "DHL", "USPS", "XPO Logistics", 
        "J.B. Hunt", "C.H. Robinson", "Schneider", "Werner", "YRC Freight"
    ]
    return random.choice(carriers)

def generate_random_standard_customer():
    customers = [
    'Walmart', 'Target', 'Costco', 'Kroger', 'Albertsons',
    'Safeway', 'Whole Foods', 'Sam\'s Club', 'Publix', 'Aldi'
]
    return random.choice(customers)

def main():
    # Get existing invoice numbers from Deductions model
    existing_invoice_numbers = set(Deductions.objects.values_list('invoice_number', flat=True))
    
    # Set date range
    start_date = datetime(2024, 1, 1).date()
    end_date = datetime(2025, 6, 13).date()  # Current date
    
    print("Creating invoices for existing deductions...")
    for invoice_num in existing_invoice_numbers:
        # For each invoice number, create 1-5 SKU lines
        invoice_date = generate_random_date(start_date, end_date)
        order_number = generate_random_order()
        bol = generate_random_bol()
        carrier = generate_random_carrier()
        
        # Generate multiple SKUs for this invoice (1-5 SKUs per invoice)
        num_skus = random.randint(1, 5)
        for _ in range(num_skus):
            billed_qty = random.randint(1, 1000)
            net_amount = generate_random_net_amount()
            gross_amount = (net_amount * Decimal('1.05')).quantize(Decimal('0.01'))
            
            Invoice.objects.create(
                invoice_number=invoice_num,
                invoice_date=invoice_date,  # Use same date for all SKUs
                order_number=order_number,  # Use same order for all SKUs
                bol=bol,                   # Use same BOL for all SKUs
                carrier=carrier,           # Use same carrier for all SKUs
                sku=generate_random_sku(),
                billed_qty=billed_qty,
                gross_amount=gross_amount,
                net_amount=net_amount,
                standard_customer=generate_random_standard_customer()
            )
    
    # Calculate how many additional lines we need
    existing_count = Invoice.objects.count()
    additional_needed = max(0, 1000 - existing_count)
    
    print("Generating additional random invoices...")
    invoices_created = 0
    while invoices_created < additional_needed:
        invoice_num = generate_random_invoice_number()
        invoice_date = generate_random_date(start_date, end_date)
        order_number = generate_random_order()
        bol = generate_random_bol()
        carrier = generate_random_carrier()
        
        # Generate 1-5 SKUs for this invoice
        num_skus = min(random.randint(1, 5), additional_needed - invoices_created)
        for _ in range(num_skus):
            billed_qty = random.randint(1, 1000)
            net_amount = generate_random_net_amount()
            gross_amount = (net_amount * Decimal('1.05')).quantize(Decimal('0.01'))
            
            Invoice.objects.create(
                invoice_number=invoice_num,
                invoice_date=invoice_date,
                order_number=order_number,
                bol=bol,
                carrier=carrier,
                sku=generate_random_sku(),
                billed_qty=billed_qty,
                gross_amount=gross_amount,
                net_amount=net_amount,
                standard_customer=generate_random_standard_customer()
            )
            invoices_created += 1

    print(f"Total invoice lines generated: {Invoice.objects.count()}")
    print(f"Unique invoice numbers: {Invoice.objects.values('invoice_number').distinct().count()}")

if __name__ == "__main__":
    main()
