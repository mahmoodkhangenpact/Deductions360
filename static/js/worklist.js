$(document).ready(function () {
    // Initialize DataTables with browser-agnostic options
    const tables = $('table.data-table').DataTable({
        dom: '<"d-flex align-items-center justify-content-between mb-3"<"d-flex align-items-center"l<"ml-2"B>>f>' +
             '<"row"<"col-sm-12"tr>>' +
             '<"row"<"col-sm-12 col-md-5"i><"col-sm-12 col-md-7"p>>',
        buttons: [
            {
                extend: 'copy',
                className: 'btn btn-sm btn-primary'
            },
            {
                extend: 'csv',
                className: 'btn btn-sm btn-success'
            },
            {
                extend: 'excel',
                className: 'btn btn-sm btn-info'
            },
            {
                extend: 'print',
                className: 'btn btn-sm btn-warning'
            }
        ],
        columnDefs: [
            {
                targets: '_all',
                className: 'text-nowrap',
                autoWidth: true
            },
            {
                targets: 0,  // First column
                width: 'auto',
                className: 'text-nowrap min-w-150'  // Minimum width class
            }
        ],
        responsive: true,
        autoWidth: true,
        pageLength: 10,
        lengthMenu: [5, 10, 25, 50, 100],
        order: [[0, 'desc']],
        language: {
            search: "_INPUT_",
            searchPlaceholder: "Search..."
        }
    });

 

    // Use jQuery to handle modal events consistently across browsers
    $(document).on('click', '.edit-deduction', function(e) {
        e.preventDefault();
        const invoiceNumber = $(this).data('invoice');
        const row = $(this).closest('tr');
        
        // Get all field values from the row
        const fields = {};
        row.find('td').each(function() {
            const fieldName = $(this).data('field');
            if (fieldName) {
                // Special handling for invoice number
                if (fieldName === 'invoice_number') {
                    fields[fieldName] = invoiceNumber; // Use the data-invoice value
                } else {
                    fields[fieldName] = $(this).text().trim();
                }
            }
        });

        console.log('Invoice Number:', invoiceNumber); // Debug log
        console.log('Fields:', fields); // Debug log
        
        // Set invoice number in both header and form
        $('#invoice_number_display').text(invoiceNumber);
        $('#invoice_number').val(invoiceNumber); // Make sure this is set
        
        // Set other field values
        Object.keys(fields).forEach(fieldName => {
            const input = $(`#${fieldName}`);
            if (input.length) {
                input.val(fields[fieldName]);
            }
        });
        
        // Load initial document
        loadDocument('invoice', invoiceNumber);
        
        // Show modal
        $('#deductionDetailModal').modal('show');
    });

    // Handle modal close events
    $('#deductionDetailModal').on('hidden.bs.modal', function () {
        // Clear form fields
        $('#deductionForm')[0].reset();
        // Clear document viewer
        $('#docViewer').attr('src', '');
        
        // Clean up modal state
        $(this).removeData('bs.modal');
        $('body').removeClass('modal-open').css('overflow', '');
    });

    // Handle close button clicks
    $('.close, button[data-dismiss="modal"]').on('click', function() {
        $('#deductionDetailModal').modal('hide');
    });

    // Filter handling
    $('#applyWorklistFilters').on('click', function() {
        tables.draw();
    });

    $('#resetWorklistFilters').on('click', function() {
        $('#worklist-filter-form')[0].reset();
        tables.draw();
    });

    // Add this function to get column indexes from table headers
    function getColumnIndexes(tableId) {
        const indexes = {};
        $(`#${tableId} thead th`).each(function(index) {
            const columnName = $(this).text().trim().toLowerCase().replace(/\s+/g, '_');
            indexes[columnName] = index;
        });
        return indexes;
    }

    // Custom filter logic
    $.fn.dataTable.ext.search.push(function (settings, data, dataIndex) {
        const activeTableId = $('.tab-pane.active table.dataTable[id]').attr('id');
        if (!activeTableId || settings.sTableId !== activeTableId) {
            return true;
        }

        // Get column indexes from current active table
        const columnIndexes = getColumnIndexes(activeTableId);

        // Use the dynamic indexes
        const tableCustomer = data[columnIndexes['standard_customer']] || '';
        const tableStatus = data[columnIndexes['status']] || '';
        const tableReason = data[columnIndexes['deduction_reason']] || '';
        const tableValidation = data[columnIndexes['validation_status']] || '';
        const tableDeductionDate = data[columnIndexes['deduction_date']] || '';
        const tableDeductionAmount = parseFloat(data[columnIndexes['deducted_amount']]) || 0;
        
        const customerFilter = $('#customerFilter').val();
        const statusFilter = $('#statusFilter').val();
        const reasonFilter = $('#reasonFilter').val();
        const validationFilter = $('#validationFilter').val();
        const deductionStartDate = $('#deductionStartDate').val();
        const deductionEndDate = $('#deductionEndDate').val();
        const deductionAmountRange = $('#deductionAmountRange').val();

        if (customerFilter && customerFilter.trim().toLowerCase() !== tableCustomer.trim().toLowerCase()) {
            return false;
        }

        if (statusFilter && statusFilter.trim().toLowerCase() !== tableStatus.trim().toLowerCase()) {
            return false;
        }

        if (reasonFilter && reasonFilter.trim().toLowerCase() !== tableReason.trim().toLowerCase()) {
            return false;
        }

        if (validationFilter && validationFilter.trim().toLowerCase() !== tableValidation.trim().toLowerCase()) {
            console.log(tableValidation,validationFilter);
            return false;
        }

        if (deductionStartDate && new Date(tableDeductionDate) < new Date(deductionStartDate)) {
            return false;
        }

        if (deductionEndDate && new Date(tableDeductionDate) > new Date(deductionEndDate)) {
            return false;
        }

        if (deductionAmountRange) {
            const [min, max] = deductionAmountRange.split('-').map(v => parseFloat(v));
            if (max) {
                if (tableDeductionAmount < min || tableDeductionAmount > max) return false;
            } else {
                if (tableDeductionAmount < min) return false;
            }
        }
        
        return true;
    });

    // Add document type switching handler
    $('.document-controls .btn').on('click', function() {
        const docType = $(this).data('doc-type');
        const invoiceNumber = $('#invoice_number').val();
        if (invoiceNumber) {
            loadDocument(docType, invoiceNumber);
        }
    });

    // Function to load documents
    function loadDocument(docType, invoiceNumber) {
        const url = `/documents/${docType}/${invoiceNumber}/`;
        
        // Show loading state
        $('#documentPreview').addClass('loading');
        
        fetch(url)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Document not found (${response.status})`);
                }
                return response.blob();
            })
            .then(blob => {
                const objectUrl = URL.createObjectURL(blob);
                
                // Clear previous content
                $('#documentPreview').empty();
                
                // Create and append new iframe
                const iframe = $('<iframe>', {
                    id: 'docViewer',
                    src: objectUrl,
                    style: 'width: 100%; height: 100%; border: none;'
                });
                
                $('#documentPreview').append(iframe);
                
                // Clean up the old ObjectURL when the iframe loads
                iframe.on('load', function() {
                    URL.revokeObjectURL(objectUrl);
                });
            })
            .catch(error => {
                console.error('Error loading document:', error);
                $('#documentPreview').html(`
                    <div class="alert alert-warning m-3">
                        No ${docType} document found for invoice ${invoiceNumber}
                    </div>
                `);
            })
            .finally(() => {
                $('#documentPreview').removeClass('loading');
                // Update active button state
                $('.document-controls .btn').removeClass('active');
                $(`.document-controls .btn[data-doc-type="${docType}"]`).addClass('active');
            });
    }

    // Handle form submission
    $('#saveDeductionChanges').on('click', function(e) {
        e.preventDefault();
        
        // Get all form data
        const formData = {};
        $('#deductionForm').serializeArray().forEach(item => {
            // Special handling for date fields
            if (item.name === 'deduction_date' || item.name === 'date_worked' || item.name === 'billback_date') {
                // Convert from MM/DD/YY to YYYY-MM-DD
                const dateParts = item.value.split('/');
                if (dateParts.length === 3) {
                    const year = dateParts[2].length === 2 ? '20' + dateParts[2] : dateParts[2];
                    const month = dateParts[0].padStart(2, '0');
                    const day = dateParts[1].padStart(2, '0');
                    formData[item.name] = `${year}-${month}-${day}`;
                } else {
                    formData[item.name] = item.value;
                }
            } else {
                formData[item.name] = item.value;
            }
        });

        // Add deduction_reference as the key identifier
        formData.identifier = $('#deduction_reference').val().trim();

        console.log('Submitting form data:', formData); // Debug log

        // Send AJAX request
        $.ajax({
            url: '/update_workflow/',
            type: 'POST',
            data: JSON.stringify(formData),
            contentType: 'application/json',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            },
            success: function(response) {
                if (response.success) {
                    // Close the modal
                    $('#deductionDetailModal').modal('hide');
                    
                    // Simply reload the page to refresh the table
                    window.location.reload();
                    
                    // Show success message
                    alert('Workflow updated successfully');
                } else {
                    alert(response.error || 'Error updating workflow');
                }
            },
            error: function(xhr, status, error) {
                console.error('Error:', xhr.responseJSON || error);
                alert('Error updating workflow: ' + (xhr.responseJSON?.error || error));
            }
        });
    });

    // Helper function to get CSRF token
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});