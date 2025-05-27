from django.db import models

# Create your models here.
class workflow(models.Model):
    #fields from deductions
    ids = models.CharField(max_length=255, blank=True, null=True)
    standard_customer = models.CharField(max_length=255, blank=True, null=True)
    deduction_reference = models.CharField(max_length=255, blank=True, null=True)
    invoice_number = models.CharField(max_length=255, blank=True, null=True)

    # fields from backup
    invoice_number = models.CharField(max_length=255, blank=True, null=True)
    deducted_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    deducted_qty = models.IntegerField(blank=True, null=True)
    deducted_price_per_qty = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    deduction_date = models.DateField(blank=True, null=True)
    deduction_reason = models.TextField(blank=True, null=True)

    #fields from invoice
    billed_qty = models.IntegerField(blank=True, null=True)
    gross_price_per_qty = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    net_price_per_qty = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    
    carrier = models.CharField(max_length=255, blank=True, null=True)
    #fields from POD
    shortage = models.IntegerField(blank=True, null=True)
    damage = models.IntegerField(blank=True, null=True)
    returns = models.IntegerField(blank=True, null=True)
    overage = models.IntegerField(blank=True, null=True)
    net_shortage = models.IntegerField(blank=True, null=True)
    
    customer_sign = models.CharField(max_length=255, blank=True, null=True)
    carrier_sign = models.CharField(max_length=255, blank=True, null=True)
    subject_to_count = models.CharField(max_length=255, blank=True, null=True)

    #calculated fields
    missing_data = models.CharField(max_length=20, null=True)
    no_shortage_in_pod = models.CharField(max_length=20, null=True)
    invalid_amt_1 = models.DecimalField(max_digits=10, decimal_places=2,null=True)
    partial_shortage_in_pod = models.CharField(max_length=20, null=True)
    invalid_amt_2 = models.DecimalField(max_digits=10, decimal_places=2,null=True)
    deducted_sku_is_not_invoiced = models.CharField(max_length=20, null=True)
    invalid_amt_3 = models.DecimalField(max_digits=10, decimal_places=2,null=True)
    pricing_variance = models.CharField(max_length=20, null=True)
    invalid_amt_4 = models.DecimalField(max_digits=10, decimal_places=2,null=True)
    validation_status = models.CharField(max_length=20, null=True)
    invalid_amount = models.DecimalField(max_digits=10, decimal_places=2,null=True)
    valid_amount = models.DecimalField(max_digits=10, decimal_places=2,null=True)
    invalid_reason =models.CharField(max_length=50, null=True, blank=True)
    billback_package = models.FileField(upload_to='media/billback_packages/', default='NoFile.zip')
    billback_date = models.DateField(blank=True, null=True)
    billback_id = models.CharField(max_length=50, null=True, blank=True)
    customer_response = models.CharField(max_length=50, null=True, blank=True)
    repayment_reference = models.CharField(max_length=50, null=True, blank=True)
    repayment_amount = models.DecimalField(max_digits=10, decimal_places=2,null=True)
    final_status = models.CharField(max_length=50, null=True, blank=True)
    product_substitution =models.CharField(max_length=50, null=True, blank=True)
    combined_shipment =models.CharField(max_length=50, null=True, blank=True)
    order_split =models.CharField(max_length=50, null=True, blank=True)
    load_sequencing =models.CharField(max_length=50, null=True, blank=True)
    unit_of_measurement =models.CharField(max_length=50, null=True, blank=True)
    deducted_at_higher_price = models.CharField(max_length=50, null=True, blank=True)
    date_worked = models.DateField(blank=True, null=True)  # New field for the date worked

    STATUS_CHOICES = [
        ('Pending Validation', 'Pending Validation'),
        ('Validated', 'Validated'),
        ('Billed Back', 'Billed Back'),
        ('Recovered', 'Recovered'),
    ]

    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Pending Validation')

    def __str__(self):
        return f"Workflow #{self.id} - {self.status}"