from osd.models import workflow
from datetime import datetime

records = workflow.objects.all()
for record in records:
    if record.deduction_date:
        try:
            # Convert mm/dd/yyyy to yyyy-mm-dd
            formatted_date = datetime.strptime(record.deduction_date, '%m/%d/%Y').date()
            record.deduction_date = formatted_date
            record.save()
        except ValueError:
            print(f"Invalid date format for record {record.id}: {record.deduction_date}")