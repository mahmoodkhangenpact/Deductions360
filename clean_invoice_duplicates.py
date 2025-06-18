from osd.models import Invoice

def clean_invoice_duplicates():
    # Identify duplicate invoice numbers
    duplicates = Invoice.objects.values('invoice_number').annotate(count=models.Count('id')).filter(count__gt=1)

    for duplicate in duplicates:
        invoice_number = duplicate['invoice_number']
        # Get all entries with the duplicate invoice number
        invoices = Invoice.objects.filter(invoice_number=invoice_number)
        # Keep the first entry and delete the rest
        invoices.exclude(id=invoices.first().id).delete()

if __name__ == "__main__":
    clean_invoice_duplicates()
    print("Duplicate entries in Invoice table cleaned up.")
