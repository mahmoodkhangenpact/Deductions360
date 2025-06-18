import os
import django
import random
from osd.models import Deductions

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'deductions360.settings')
django.setup()

def update_recovered_amounts():
    deductions = Deductions.objects.filter(invalid_amount__gt=0)
    for deduction in deductions:
        recovery_percentage = random.uniform(0.8, 1.0)  # Random percentage between 80% and 100%
        deduction.recovered_amount = deduction.invalid_amount * recovery_percentage
        deduction.save()

if __name__ == "__main__":
    update_recovered_amounts()
    print("Recovered amounts updated successfully.")