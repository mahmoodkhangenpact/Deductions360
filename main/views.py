from django.shortcuts import render
from osd.models import Deductions, workflow, Invoice
from django.db.models import Sum, Count, Q, Case, When, Value, CharField
from django.db.models.functions import TruncMonth, ExtractYear, Concat
from django.http import JsonResponse, HttpResponse, FileResponse
from django.contrib.auth.decorators import login_required
from django.db.models.fields import Field
import json
from datetime import datetime, timedelta
from django.conf import settings
import os
from pathlib import Path
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import mimetypes
import zipfile
# from .utils import create_document_package
from wsgiref.util import FileWrapper
import random
from django.http import JsonResponse

@login_required(login_url='login') 
def index(request):
    records = workflow.objects.all()  # Fetch all records from the workflow model
    for record in records:
        try:
            record.invoice_number = str(int(float(record.invoice_number)))
        except (ValueError, TypeError):
            record.invoice_number = record.invoice_number  # Keep the original value if conversion fails
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
    for entry in daily_data:
        print(f"Date Worked: {entry['date_worked']}, Transactions: {entry['transactions']}")

    # Format dates as mm/dd/yy, ensuring date_worked is not None
    dates = [entry['date_worked'].strftime('%m/%d/%y') for entry in daily_data if entry['date_worked'] is not None]
    print("Dates", dates)
    transactions = [entry['transactions'] for entry in daily_data]
    

    # Prepare data for the daily transactions worked chart
    daily_transactions_data = {
        'dates': dates,
        'transactions': transactions
    }
    
    # Serialize the data to JSON
    daily_transactions_data_json = json.dumps(daily_transactions_data)

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
        'transactions': json.dumps(transactions),
        'daily_transactions_data': daily_transactions_data_json,  # Pass transactions for the chart
        'donut_chart_data': donut_chart_data_json,
        'deductions_sum': totals['deductions_sum'] or 0,
        'valid_sum': totals['valid_sum'] or 0,
        'invalid_sum': totals['invalid_sum'] or 0,
        'recovered_sum': totals['recovered_sum'] or 0,
    }
    
    return render(request, 'index.html', context)



def daily_transactions_chart_data(request):
    daily_data = (
        workflow.objects.filter(date_worked__isnull=False)
        .values('date_worked')
        .annotate(transactions=Count('id'))
        .order_by('date_worked')
    )

    dates = [entry['date_worked'].strftime('%m/%d/%y') for entry in daily_data if entry['date_worked']]
    transactions = [entry['transactions'] for entry in daily_data]

    return JsonResponse({
        'dates': dates,
        'transactions': transactions,
    })


# Views for handling AJAX chart data requests
@login_required(login_url='login')
def filtered_chart_data(request):
    try:
        # Get filter parameters
        customer = request.GET.get('standard_customer', '')
        status = request.GET.get('validation_status', '')
        from_date = request.GET.get('deduction_date_from', '')
        to_date = request.GET.get('deduction_date_to', '')
        amount_min = request.GET.get('deducted_amount_min', '')
        amount_max = request.GET.get('deducted_amount_max', '')
        search = request.GET.get('search[value]', '')
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 10))

        # Base queryset using workflow model
        queryset = workflow.objects.all()

        # Apply filters
        if customer:
            queryset = queryset.filter(standard_customer__icontains=customer)
        if status:
            queryset = queryset.filter(validation_status=status)
        if from_date:
            queryset = queryset.filter(deduction_date__gte=from_date)
        if to_date:
            queryset = queryset.filter(deduction_date__lte=to_date)
        if amount_min:
            queryset = queryset.filter(deducted_amount__gte=float(amount_min))
        if amount_max:
            queryset = queryset.filter(deducted_amount__lte=float(amount_max))
            
        # Apply search
        if search:
            queryset = queryset.filter(
                Q(invoice_number__icontains=search) |
                Q(standard_customer__icontains=search) |
                Q(validation_status__icontains=search)
            )

        # Get data for donut chart (top 10 customers)
        donut_data = queryset.values('standard_customer').annotate(
            total_deductions=Sum('deducted_amount')
        ).order_by('-total_deductions')[:10]

        # Get data for daily transactions chart
        daily_data = (
            queryset.filter(date_worked__isnull=False)
            .values('date_worked')
            .annotate(transactions=Count('id'))
            .order_by('date_worked')
        )

        # Calculate card totals
        totals = queryset.aggregate(
            deductions=Sum('deducted_amount'),
            valids=Sum('valid_amount'),
            invalids=Sum('invalid_amount'),
            recovered=Sum('invalid_amount')  # Using invalid_amount for recovered, adjust if needed
        )        # Get total count before pagination
        total_records = queryset.count()
        
        # Apply pagination
        records = queryset[start:start + length]
        
        # Format records for DataTables
        data = []
        for record in records:
            try:
                invoice = str(int(float(record.invoice_number)))
            except (ValueError, TypeError):
                invoice = record.invoice_number
                
            data.append([
                invoice,
                record.standard_customer,
                f"${record.deducted_amount:,.2f}",
                record.validation_status,
                record.deduction_date.strftime('%Y-%m-%d') if record.deduction_date else ''
            ])
        
        # Format the response for DataTables with additional chart data
        response_data = {
            'draw': int(request.GET.get('draw', 1)),
            'recordsTotal': total_records,
            'recordsFiltered': total_records,
            'data': data,
            'card_data': {
                'deductions': float(totals['deductions'] or 0),
                'valids': float(totals['valids'] or 0),
                'invalids': float(totals['invalids'] or 0),
                'recovered': float(totals['recovered'] or 0)
            },
            'donut_chart_data': {
                'labels': [entry['standard_customer'] for entry in donut_data],
                'data': [float(entry['total_deductions']) for entry in donut_data]
            },
            'daily_transactions': {
                'dates': [entry['date_worked'].strftime('%m/%d/%y') for entry in daily_data if entry['date_worked'] is not None],
                'transactions': [entry['transactions'] for entry in daily_data]
            }
        }

        return JsonResponse(response_data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

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

@login_required(login_url='login')
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

@login_required(login_url='login')
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

@login_required(login_url='login')
def insights_view(request):
    # Get filter parameters
    customer = request.GET.get('standard_customer', '')
    status = request.GET.get('validation_status', '')
    reason = request.GET.get('deduction_reason', '')
    date_range = request.GET.get('date_range', '')

    # Base queryset for Deductions and Invoices
    deductions_queryset = Deductions.objects.all()
    invoices_queryset = Invoice.objects.all()

    # Apply filters to Deductions
    if customer:
        deductions_queryset = deductions_queryset.filter(standard_customer__icontains=customer)
    if status:
        deductions_queryset = deductions_queryset.filter(validation_status=status)
    if reason:
        deductions_queryset = deductions_queryset.filter(deduction_reason=reason)
    if date_range and date_range != 'all':
        try:
            if date_range != 'custom':
                days = int(date_range)
                start_date = datetime.now() - timedelta(days=days)
                deductions_queryset = deductions_queryset.filter(deduction_date__gte=start_date)
        except ValueError:
            pass

    # Apply filters to Invoices based on customer and date range
    if customer:
        invoices_queryset = invoices_queryset.filter(standard_customer__icontains=customer)
    if date_range and date_range != 'all':
        try:
            if date_range != 'custom':
                days = int(date_range)
                start_date = datetime.now() - timedelta(days=days)
                invoices_queryset = invoices_queryset.filter(invoice_date__gte=start_date)
        except ValueError:
            pass

    # Define current year for filtering
    current_year = datetime.now().year

    # Calculate total revenue dynamically based on filtered Invoice queryset
    total_revenue = float(invoices_queryset.aggregate(Sum('gross_amount'))['gross_amount__sum'] or 0)
    ytd_revenue = float(invoices_queryset.filter(invoice_date__year=current_year).aggregate(Sum('gross_amount'))['gross_amount__sum'] or 0)

    total_deductions = float(deductions_queryset.aggregate(Sum('deducted_amount'))['deducted_amount__sum'] or 0)
    ytd_deductions = float(deductions_queryset.filter(deduction_date__year=current_year).aggregate(Sum('deducted_amount'))['deducted_amount__sum'] or 0)

    valid_deductions = float(deductions_queryset.filter(validation_status='Valid').aggregate(Sum('valid_amount'))['valid_amount__sum'] or 0)
    invalid_deductions = float(deductions_queryset.filter(validation_status='Invalid').aggregate(Sum('invalid_amount'))['invalid_amount__sum'] or 0)
    pending_deductions = float(deductions_queryset.filter(validation_status='Pending').aggregate(Sum('deducted_amount'))['deducted_amount__sum'] or 0)

    deductions_percentage = (total_deductions / total_revenue * 100) if total_revenue > 0 else 0
    deductions_percentage = round(deductions_percentage, 2)  # Round to 2 decimal places

    # Calculate quarterly data for deductions
    quarterly_data = (
        deductions_queryset
        .annotate(
            quarter=Concat(
                ExtractYear('deduction_date'),
                Value(' Q'),
                Case(
                    When(deduction_date__month__lte=3, then=Value('1')),
                    When(deduction_date__month__lte=6, then=Value('2')),
                    When(deduction_date__month__lte=9, then=Value('3')),
                    default=Value('4'),
                ),
                output_field=CharField(),
            )
        )
        .values('quarter', 'open_closed')
        .annotate(amount=Sum('deducted_amount'))
        .order_by('quarter')
    )

    quarters = sorted(list(set(item['quarter'] for item in quarterly_data)))
    open_amounts = []
    closed_amounts = []

    for quarter in quarters:
        quarter_data = {item['open_closed']: item['amount'] for item in quarterly_data if item['quarter'] == quarter}
        open_amounts.append(float(quarter_data.get('Open', 0)))
        closed_amounts.append(float(quarter_data.get('Closed', 0)))

    # Calculate tolerance distribution
    tolerance_ranges = [
        ('0-100', 0, 100),
        ('100-500', 100, 500),
        ('500-1000', 500, 1000),
        ('1000-5000', 1000, 5000),
        ('5000-10000', 5000, 10000),
        ('10000+', 10000, float('inf'))
    ]    
    tolerance_data = {
        'labels': [],
        'ut_data': [],
        'ot_data': []
    }

    # Calculate total under tolerance amount using deductions_queryset
    total_ut_amount = deductions_queryset.filter(tolerance='UT').aggregate(total=Sum('deducted_amount'))['total'] or 0

    # Update tolerance distribution calculation
    for label, min_val, max_val in tolerance_ranges:
        count_query = deductions_queryset.filter(deducted_amount__gt=min_val)
        if max_val != float('inf'):
            count_query = count_query.filter(deducted_amount__lte=max_val)

        tolerance_data['labels'].append(label)
        tolerance_data['ut_data'].append(count_query.filter(tolerance='UT').count())
        tolerance_data['ot_data'].append(count_query.filter(tolerance='OT').count())
    
    tolerance_data['total_ut'] = float(total_ut_amount)

    reason_chart_data = get_reason_chart_data(deductions_queryset)
    topcustomer_chart_data = get_topcustomers_chart_data(deductions_queryset)

    # Ensure total_revenue dynamically updates based on filtered Invoice queryset
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'totals': {
                'total_revenue': total_revenue,  # Fix: Include total_revenue in the AJAX response
                'ytd_revenue': ytd_revenue,
                'ytd_deductions': ytd_deductions,
                'deductions_percentage': deductions_percentage,
                'total_deductions': total_deductions,
                'valid_deductions': valid_deductions,
                'invalid_deductions': invalid_deductions,
                'under_tolerance': float(total_ut_amount),
                'pending_deductions': pending_deductions
            },
            'quarters': quarters,
            'open_amounts': open_amounts,
            'closed_amounts': closed_amounts,
            'tolerance_data': tolerance_data,
            'reason_chart_data': reason_chart_data,
            'topcustomer_chart_data': topcustomer_chart_data,  # Added to AJAX response
            'filter_options': {
                'customers': standard_customers,
                'statuses': statuses,
                'reasons': reasons
            }
        })

 
    context = {
        'standard_customers': standard_customers,
        'statuses': statuses,
        'selected_customer': customer,
        'selected_status': status,
        'reasons': reasons,
        'selected_reason': reason,
        'selected_date_range': date_range,
        'total_revenue': total_revenue,
        'ytd_revenue': total_deductions,
        'ytd_deductions': ytd_deductions,
        'deductions_percentage': deductions_percentage,
        'total_deductions': total_deductions,
        'valid_deductions': valid_deductions,
        'invalid_deductions': invalid_deductions,
        'under_tolerance': total_ut_amount,
        'pending_deductions': pending_deductions,
        'quarters': json.dumps(quarters),
        'open_amounts': json.dumps(open_amounts),
        'closed_amounts': json.dumps(closed_amounts),
        'tolerance_data': json.dumps(tolerance_data),
        'reason_chart_data': json.dumps(reason_chart_data),
        'topcustomer_chart_data': json.dumps(topcustomer_chart_data)
    }
    
    return render(request, 'insights.html', context)

def get_trends_data(queryset):
    trends = queryset.values('deduction_date')\
        .annotate(total=Sum('deducted_amount'))\
        .order_by('deduction_date')
    
    return {
        'labels': [t['deduction_date'].strftime('%Y-%m-%d') for t in trends],
        'deductions': [float(t['total'] or 0) for t in trends]
    }

def get_status_distribution(queryset):
    status_dist = queryset.values('validation_status')\
        .annotate(total=Count('id'))
    
    return {
        'labels': [s['validation_status'] for s in status_dist],
        'values': [s['total'] for s in status_dist]
    }

def get_top_customers(queryset):
    customers = queryset.values('standard_customer')\
        .annotate(total=Sum('deducted_amount'))\
        .order_by('-total')[:10]
    
    return {
        'labels': [c['standard_customer'] for c in customers],
        'values': [float(c['total'] or 0) for c in customers]
    }

def get_recovery_rates(queryset):
    customers = queryset.values('standard_customer')\
        .annotate(
            total=Sum('deducted_amount'),
            recovered=Sum('deducted_amount', filter=Q(status='Recovered'))
        )\
        .order_by('-total')[:10]
    
    return {
        'labels': [c['standard_customer'] for c in customers],
        'values': [
            float(c['recovered'] or 0) / float(c['total'] or 1) * 100 
            for c in customers
        ]
    }

def get_reason_chart_data(deductions_queryset):
    # Get reasons distribution using deductions_queryset
    reason_data = (
        deductions_queryset
        .values('deduction_reason')
        .annotate(total_amount=Sum('deducted_amount'))
        .order_by('-total_amount')
    )

    # Calculate additional data for horizontal bar charts
    invalid_data = (
        deductions_queryset
        .values('deduction_reason')
        .annotate(
            invalid_amount=Sum('invalid_amount'),
            recovered_amount=Sum('recovered_amount')  # Include recovered_amount in the query
        )
        .order_by('-invalid_amount')
    )

    recovery_data = [
        {
            'deduction_reason': item['deduction_reason'],
            'recovery_percentage': round((float(item['recovered_amount'] or 0) / float(item['invalid_amount'] or 1)) * 100, 2)  # Calculate recovery percentage
        }
        for item in invalid_data
    ]

    return {
        'labels': [item['deduction_reason'] for item in reason_data],
        'data': [float(item['total_amount'] or 0) for item in reason_data],
        'invalid_data': [float(item['invalid_amount'] or 0) for item in invalid_data],
        'recovery_data': [item['recovery_percentage'] for item in recovery_data]
    }

def get_topcustomers_chart_data(deductions_queryset):
    # Debugging logs for deductions_queryset
    # print("Debugging deductions_queryset:", deductions_queryset)

    topcustomers_data = (
        deductions_queryset
        .values('standard_customer')
        .annotate(total_amount=Sum('deducted_amount'))
        .order_by('-total_amount')
    )

    invalid_data = (
        deductions_queryset
        .values('standard_customer')
        .annotate(
            invalid_amount=Sum('invalid_amount'),
            recovered_amount=Sum('recovered_amount')  # Include recovered_amount in the query
        )
        .order_by('-invalid_amount')
    )

    recovery_data = [
        {
            'standard_customer': item['standard_customer'],
            'recovery_percentage': round((float(item['recovered_amount'] or 0) / float(item['invalid_amount'] or 1)) * 100, 2)  # Calculate recovery percentage
        }
        for item in invalid_data
    ]

    return {
        'labels': [item['standard_customer'] for item in topcustomers_data],
        'data': [float(item['total_amount'] or 0) for item in topcustomers_data],
        'invalid_data': [float(item['invalid_amount'] or 0) for item in invalid_data],
        'recovery_data': [item['recovery_percentage'] for item in recovery_data]
    }

# Ensure standard_customers and statuses are defined before usage
standard_customers = sorted(set(
    Deductions.objects.values_list('standard_customer', flat=True)
    .exclude(standard_customer__isnull=True)
    .exclude(standard_customer='')
    .exclude(standard_customer__exact=' ')  # Exclude single space values
))

statuses = sorted(set(
    Deductions.objects.values_list('validation_status', flat=True)
    .exclude(validation_status__isnull=True)
    .exclude(validation_status='')
    .exclude(validation_status__exact=' ')  # Exclude single space values
))
reasons = sorted(set(
    Deductions.objects.values_list('deduction_reason', flat=True)
    .exclude(deduction_reason__isnull=True)
    .exclude(deduction_reason='')
    .exclude(deduction_reason__exact=' ')  # Exclude single space values
))
