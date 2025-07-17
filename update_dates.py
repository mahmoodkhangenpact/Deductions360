from osd.models import workflow
from datetime import datetime

for row in workflow.objects.all():
    if isinstance(row.deduction_date, str):
        try:
            row.deduction_date = datetime.strptime(row.deduction_date, "%m/%d/%Y").date()
            row.save()
        except Exception as e:
            print(f"Error parsing date for ID {row.id}: {e}")
