import csv
import random
from datetime import datetime, timedelta

customers = [
    "Amazon", "Target", "Walmart", "Costco", "Supervalu", "Kroger", "Dollar General", "BJ's", "Meijer"
]
regions = ["West", "Midwest", "South", "East", "Northeast", "Southeast", "Northwest", "Southwest"]
deduction_reasons = ["OSD"]
validation_statuses = ["invalid", "valid", "partially invalid"]
carrier_signs = ["yes"]
customer_signs = ["yes"]
subject_to_count = ["no"]
rca_reasons = [
    "product substitution", "combined shipment", "order split", "load sequencing", "unit_of_measurement", "price mismatch"
]
warehouses = ["WH1", "WH2", "WH3", "WH4"]

def random_date(start, end):
    delta = end - start
    return start + timedelta(days=random.randint(0, delta.days))

start_date = datetime.strptime("07/01/2024", "%m/%d/%Y")
end_date = datetime.strptime("06/30/2025", "%m/%d/%Y")

invoice_base = 10000
invoice_count = 5000  # Number of unique invoices

# Step 1: Assign a random date to each invoice_number
invoice_dates = {}
for inv in range(invoice_base + 1, invoice_base + invoice_count + 1):
    invoice_dates[inv] = random_date(start_date, end_date).strftime("%m/%d/%Y")

with open("mock_deductions2.csv", "w", newline="") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow([
        "invoice_number", "deduction_amount", "deduction_date", "sku", "deducted_qty", "standard_customer",
        "deduction_reason", "billed_qty", "net_price_per_qty", "pod_shortage", "customer_sign", "carrier_sign",
        "subject_to_count", "validation_status", "invalid_reason", "invalid_amount", "valid_amount", "rca",
        "warehouse", "region"
    ])
    for i in range(1, 20001):
        invoice_number = invoice_base + random.randint(1, invoice_count)
        deduction_amount = round(random.uniform(50, 5000), 2)
        deduction_date = invoice_dates[invoice_number]
        sku = f"SKU{random.randint(100,150)}"
        deducted_qty = random.randint(1, 50)
        standard_customer = random.choice(customers)
        deduction_reason = random.choice(deduction_reasons)
        billed_qty = deducted_qty + random.randint(0, 5)
        net_price_per_qty = round(random.uniform(10, 100), 2)
        pod_shortage = random.randint(0, 5)
        customer_sign = random.choice(customer_signs)
        carrier_sign = random.choice(carrier_signs)
        subject_to_count_val = random.choice(subject_to_count)
        validation_status = random.choice(validation_statuses)
        if validation_status == "valid":
            invalid_reason = ""
            invalid_amount = 0
            valid_amount = deduction_amount
            rca = ""
        elif validation_status == "invalid":
            invalid_reason = random.choice(rca_reasons)
            invalid_amount = deduction_amount
            valid_amount = 0
            rca = invalid_reason
        else:  # partially invalid
            invalid_reason = random.choice(rca_reasons)
            invalid_amount = round(deduction_amount * random.uniform(0.1, 0.9), 2)
            valid_amount = round(deduction_amount - invalid_amount, 2)
            rca = invalid_reason
        warehouse = random.choice(warehouses)
        region = random.choice(regions)
        writer.writerow([
            invoice_number, deduction_amount, deduction_date, sku, deducted_qty, standard_customer,
            deduction_reason, billed_qty, net_price_per_qty, pod_shortage, customer_sign, carrier_sign,
            subject_to_count_val, validation_status, invalid_reason, invalid_amount, valid_amount, rca,
            warehouse, region
        ])