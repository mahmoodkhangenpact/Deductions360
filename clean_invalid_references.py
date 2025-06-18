from osd.models import workflow
import datetime
records = workflow.objects.all()
for record in records:
    if isinstance(record.date_worked, str):
        print(f"Record ID {record.id} has date_worked as a string: {record.date_worked}")
    elif isinstance(record.date_worked, datetime.date):
        print(f"Record ID {record.id} has date_worked as a date: {record.date_worked}")
    else:
        print(f"Record ID {record.id} has an unexpected type for date_worked: {type(record.date_worked)}")

