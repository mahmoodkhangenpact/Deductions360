// This script initializes a DataTable with custom filters for a dashboard.
$(document).ready(function() {
    // Initialize DataTable
    const table = $('#dashboard-table').DataTable({
        dom: '<"top"lfB>rt<"bottom"ip><"clear">',
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
        responsive: false,
        paging: true,
        pageLength: 10,
        lengthMenu: [5, 10, 25, 50, 100],
        searching: true,
        ordering: true,
        info: true,
        autoWidth: true,
        scrollX: true,
    });

    // Apply filters when the button is clicked
    $('button[type="button"]').on('click', function() {
        table.draw(); // Trigger the draw (filter) action
    });
    // Reset filters when the "Reset" button is clicked
    $('#resetFilters').on('click', function () {
    // Reset the filter form
        $('#filter-form')[0].reset();

        // Programmatically trigger the Apply Filters button
        $('button[type="button"][id="filter-button"]').click();
    }); 

    // Custom filter logic
    $.fn.dataTable.ext.search.push(function(settings, data, dataIndex) {
        const customer = $('#standard_customer').val();
        const amountFilter = $('#deducted_amount').val();
        const status = $('#validation_status').val();
        const fromDate = $('#deduction_date_from').val();
        const toDate = $('#deduction_date_to').val();

        const tableCustomer = data[1]; // Adjust index as per your actual table column order
        const tableAmount = parseFloat(data[2].replace('$', '')) || 0;
        const tableStatus = data[3];
        const tableDate = new Date(data[4]);

        // Customer filter
        if (customer && customer !== tableCustomer) return false;

        // Amount filter (exact match for now)
        if (amountFilter && parseFloat(amountFilter) !== tableAmount) return false;

        // Status filter
        if (status && status !== tableStatus) return false;

        // Date filter
        if (fromDate && tableDate < new Date(fromDate)) return false;
        if (toDate && tableDate > new Date(toDate)) return false;

        return true;
    });
});









