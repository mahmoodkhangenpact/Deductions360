from django.shortcuts import render
from osd.models import workflow  # Update import to use Workflow model
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth
import json
from django.http import JsonResponse, FileResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.forms.models import model_to_dict
from django.db.models.fields import Field
from datetime import datetime
from django.conf import settings
import os
from pathlib import Path
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import mimetypes
import zipfile
# from .utils import create_document_package
from wsgiref.util import FileWrapper

@login_required(login_url='login') 
def index(request):
    records = workflow.objects.all()  # Fetch all records from the workflow model
    for record in records:
        record.invoice_number = str(int(float(record.invoice_number)))
    standard_customers = workflow.objects.values('standard_customer').distinct()
    deducted_amounts = workflow.objects.values('deducted_amount').distinct()
    validation_statuses = workflow.objects.values('validation_status').distinct()

    # Fetch and aggregate data for the line chart (Daily Transactions Worked)
    daily_data = (
        workflow.objects.filter(date_worked__isnull=False)
        .values('date_worked')
        .annotate(transactions=Count('id'))
        .order_by('date_worked')
    )

    # Format dates as mm/dd/yy
    dates = [entry['date_worked'].strftime('%m/%d/%y') for entry in daily_data]
    transactions = [entry['transactions'] for entry in daily_data]

    # Fetch and aggregate data for the donut chart (top 10 customers)
    donut_data = workflow.objects.values('standard_customer').annotate(total_deductions=Sum('deducted_amount')).order_by('-total_deductions')[:10]
    
    # Prepare data for the donut chart
    donut_chart_data = {
        'labels': [entry['standard_customer'] for entry in donut_data],
        'data': [float(entry['total_deductions']) for entry in donut_data]  # Convert Decimal to float
    }

    # Serialize the data to JSON
    donut_chart_data_json = json.dumps(donut_chart_data)
    
    totals = workflow.objects.aggregate(
        deductions_sum=Sum('deducted_amount'),
        valid_sum=Sum('valid_amount'),
        invalid_sum=Sum('invalid_amount'),
        recovered_sum=Sum('invalid_amount'),  # Replace with actual logic if different
    )
    
    # Pass the filter data to the template
    context = {
        'records': records,
        'standard_customers': standard_customers,
        'deducted_amounts': deducted_amounts,
        'validation_statuses': validation_statuses,
        'dates': json.dumps(dates),  # Pass formatted dates for the Daily Transactions Worked chart
        'transactions': json.dumps(transactions),  # Pass transactions for the chart
        'donut_chart_data': donut_chart_data_json,
        'deductions_sum': totals['deductions_sum'] or 0,
        'valid_sum': totals['valid_sum'] or 0,
        'invalid_sum': totals['invalid_sum'] or 0,
        'recovered_sum': totals['recovered_sum'] or 0,
    }
    return render(request, 'index.html', context)

@login_required(login_url='login')
def filtered_chart_data(request):
    customer = request.GET.get('standard_customer')
    status = request.GET.get('validation_status')
    from_date = request.GET.get('deduction_date_from')
    to_date = request.GET.get('deduction_date_to')

    queryset = workflow.objects.all()

    if customer:
        queryset = queryset.filter(standard_customer=customer)
    if status:
        queryset = queryset.filter(validation_status=status)
    if from_date:
        queryset = queryset.filter(deduction_date__gte=from_date)
    if to_date:
        queryset = queryset.filter(deduction_date__lte=to_date)

    # Daily Transactions Worked data
    daily_data = (
        queryset.filter(date_worked__isnull=False)
        .values('date_worked')
        .annotate(transactions=Count('id'))
        .order_by('date_worked')
    )

    dates = [entry['date_worked'].strftime('%m/%d/%y') for entry in daily_data]
    transactions = [entry['transactions'] for entry in daily_data]

    # Donut chart data
    donut_data = queryset.values('standard_customer').annotate(total_deductions=Sum('deducted_amount')).order_by('-total_deductions')[:10]
    donut_chart_data = {
        'labels': [entry['standard_customer'] for entry in donut_data],
        'data': [float(entry['total_deductions']) for entry in donut_data]
    }

    # Card data
    totals = queryset.aggregate(
        deductions_sum=Sum('deducted_amount') or 0,
        valid_sum=Sum('valid_amount') or 0,
        invalid_sum=Sum('invalid_amount') or 0,
        recovered_sum=Sum('invalid_amount') or 0
    )

    return JsonResponse({
        'daily_transactions': {
            'dates': dates,
            'transactions': transactions,
        },
        'donut_chart_data': donut_chart_data,
        'card_data': {
            'deductions': totals['deductions_sum'],
            'valids': totals['valid_sum'],
            'invalids': totals['invalid_sum'],
            'recovered': totals['recovered_sum'],
        }
    })

@login_required(login_url='login')
def worklist_view(request):
   
    
    all_data = workflow.objects.all()
    pending = workflow.objects.filter(status='Pending Validation')
    validated = workflow.objects.filter(status='Validated')
    billed = workflow.objects.filter(status='Billed Back')
    recovered = workflow.objects.filter(status='Recovered')

    # Get all fields of the workflow model
    workflow_fields = [field for field in workflow._meta.get_fields() if isinstance(field, Field)]
    
    # Fetch unique values for filters
    unique_customers = workflow.objects.values_list('standard_customer', flat=True).distinct()
    unique_statuses = workflow.objects.values_list('status', flat=True).distinct()
    unique_reasons = workflow.objects.values_list('deduction_reason', flat=True).distinct()
    unique_validation = workflow.objects.values_list('validation_status', flat=True).distinct()

    # Define fields to hide
    hidden_fields = ['id', 'ids', 'invalid_amt_1', 'invalid_amt_2', 'invalid_amt_3', 'invalid_amt_4', 'product_substitution', 'combined_shipment',
                     'order_split', 'load_sequencing', 'unit_of_measurement', 'deducted_at_higher_price']
    readonly_fields = ['standard customer','deduction reference', 'invoice_number', 'deducted_amount', 'deducted_qty', 'deduction_date',
                        'deduction_reason', 'billed_qty', 'gross_price_per_qty','net price per qty','carrier', 'shortage', 'damage', 
                        'returns', 'overage', 'net_shortage', 'customer_sign', 'carrier_sign', 'subject_to_count', 'missing_data',
                        'no_shortage_in_pod', 'partial_shortage_in_pod', 'deducted_sku_is_not_invoiced', 'pricing_variance', 'validation_status',
                        'invalid_amount', 'valid_amount', 'invalid_reason', 'date_worked', 'status']
    tab_data = [
        {'label': 'All Deductions', 'data': all_data},
        {'label': 'Pending Validation', 'data': pending},
        {'label': 'Validated', 'data': validated},
        {'label': 'Billed Back', 'data': billed},
        {'label': 'Recovered', 'data': recovered},
    ]

    if request.GET.get('download_docs'):
        invoice_number = request.GET.get('invoice_number')
        if invoice_number:
            zip_path, error = create_document_package(invoice_number)
            if zip_path:
                wrapper = FileWrapper(open(zip_path, 'rb'))
                response = FileResponse(wrapper, content_type='application/zip')
                response['Content-Disposition'] = f'attachment; filename="invoice_{invoice_number}.zip"'
                return response
            else:
                return JsonResponse({
                    'error': error or 'Error creating document package'
                }, status=500)
    
    return render(request, 'worklist.html', {
        'tab_data': tab_data,
        'workflow_fields': workflow_fields,
        'unique_customers': unique_customers,
        'unique_statuses': unique_statuses,
        'unique_reasons': unique_reasons,
        'unique_validation': unique_validation,
        'hidden_fields': hidden_fields,
        'readonly_fields': readonly_fields,
    })

def serve_document(request, doc_type, invoice_number):
    
    # Format invoice number to handle float/decimal values
    try:
        formatted_invoice = str(int(float(invoice_number)))
    except ValueError:
        formatted_invoice = invoice_number
        
    # Define base paths for different document types
    doc_paths = {
        'invoice': settings.INVOICE_UPLOAD_PATH,
        'pod': settings.POD_UPLOAD_PATH,
        'backup': settings.BACKUP_UPLOAD_PATH
    }
    
    base_path = doc_paths.get(doc_type)
    # Check if the base path is valid
    if not base_path:
        return HttpResponse('Invalid document type', status=400)
    
    base_path = Path(base_path)
    if not base_path.exists():
        return HttpResponse('Document directory not found', status=500)
    
    # Search for files matching the invoice number
    matching_files = []
    try:
        search_pattern = f"*{formatted_invoice}*"
        for file in base_path.glob(search_pattern):
            if file.suffix.lower() in ['.pdf', '.jpg', '.jpeg', '.png']:
                matching_files.append(file)
                break  # Take the first matching file
    except Exception as e:
        return HttpResponse(f'Error accessing documents: {str(e)}', status=500)
    
    if not matching_files:
        return HttpResponse(f'No documents found for invoice {formatted_invoice}', status=404)
    
    file_path = matching_files[0]
    try:
        # Determine content type
        content_type, _ = mimetypes.guess_type(str(file_path))
        # Open and return the file
        response = FileResponse(open(file_path, 'rb'), content_type=content_type)
        response['Content-Disposition'] = f'inline; filename="{file_path.name}"'
        return response
        
    except Exception as e:
        return HttpResponse(f'Error serving document: {str(e)}', status=500)

@require_http_methods(["POST"])
def update_workflow(request):
    try:
        data = json.loads(request.body)
        deduction_reference = data.get('identifier')
        try:
            workflow_obj = workflow.objects.get(deduction_reference=deduction_reference)
            # Update fields
            for key, value in data.items():
                if hasattr(workflow_obj, key) and key not in ['identifier', 'deduction_reference']:
                    setattr(workflow_obj, key, value)
            
            workflow_obj.save()
            return JsonResponse({
                'success': True,
                'message': 'Workflow updated successfully'
            })
            
        except workflow.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': f'Workflow with reference {deduction_reference} not found'
            }, status=404)
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

def create_document_package(invoice_number):
    """
    Create a zip package containing all documents for a given invoice number
    Returns: (zip_path, error_message) tuple
    """
    try:
        # Create uploads directory if it doesn't exist
        upload_dir = Path(settings.MEDIA_ROOT) / 'document_packages'
        upload_dir.mkdir(parents=True, exist_ok=True)

        # Create zip filename using invoice number
        zip_filename = f"docs_invoice_{invoice_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        zip_path = upload_dir / zip_filename

        # Document types and their paths
        doc_types = {
            'invoice': settings.INVOICE_UPLOAD_PATH,
            'pod': settings.POD_UPLOAD_PATH,
            'backup': settings.BACKUP_UPLOAD_PATH
        }
        
        # Format invoice number
        formatted_invoice = str(int(float(invoice_number)))
        
        with zipfile.ZipFile(zip_path, 'w') as zip_file:
            for doc_type, base_path in doc_types.items():
                path = Path(base_path)
                if path.exists():
                    # Search for matching files
                    matching_files = list(path.glob(f"*{formatted_invoice}*"))
                    for file in matching_files:
                        if file.suffix.lower() in ['.pdf', '.jpg', '.jpeg', '.png']:
                            # Add file to zip with a descriptive name
                            arc_name = f"{formatted_invoice}_{doc_type}{file.suffix}"
                            zip_file.write(file, arc_name)

        return str(zip_path) if zip_path.exists() else None, None

    except Exception as e:
        error_msg = f"Error creating document package for invoice {invoice_number}: {str(e)}"
        print(error_msg)  # For server logs
        return None, error_msg

