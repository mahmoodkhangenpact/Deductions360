// This script initializes a DataTable with custom filters for a dashboard.
$(document).ready(function() {
    
    // Initialize DataTable with proper configuration
    const table = $('#dashboard-table.data-table').DataTable({
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
                className: 'text-nowrap min-w-100'  // Minimum width class
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
        },
        processing: true,
        serverSide: true,
        ajax: {
            url: '/filtered-chart-data/',
            type: 'GET',
            data: function(d) {
                return {
                    standard_customer: $('#standard_customer').val(),
                    validation_status: $('#validation_status').val(),
                    deduction_date_from: $('#deduction_date_from').val(),
                    deduction_date_to: $('#deduction_date_to').val(),
                    deducted_amount_min: $('#deducted_amount_min').val(),
                    deducted_amount_max: $('#deducted_amount_max').val(),
                    draw: d.draw,
                    start: d.start,
                    length: d.length,
                    order: d.order,
                    search: d.search
                };
            },
            
        },
        paging: true,
        searching: true,
        ordering: true,
        order: [[4, 'desc']], // Sort by date column by default
        info: true,
        scrollX: true,
        language: {
            search: "_INPUT_",
            searchPlaceholder: "Search...",
            lengthMenu: "_MENU_ records per page",
            paginate: {
                first: '«',
                previous: '‹',
                next: '›',
                last: '»'
            }
        },
        drawCallback: function(settings) {
            // Adjust column widths after each draw
            $('.dataTables_paginate > .pagination').addClass('pagination-sm');
        }
    });

    
    // Handle filter button click
    $('#filter-button').on('click', function(e) {
        e.preventDefault();
        applyFilters();
        
    });

    // Handle form submission
    $('#filter-form').on('submit', function(e) {
        e.preventDefault();
        applyFilters();
    });

    // Handle reset button
    $('#resetFilters').on('click', function() {
        $('#filter-form')[0].reset();
        applyFilters();
        
        
        
    });

    // Custom filter logic with improved matching
    $.fn.dataTable.ext.search.push(function(settings, data, dataIndex) {
        const customer = $('#standard_customer').val().toLowerCase();
        const amountMin = parseFloat($('#deducted_amount_min').val()) || 0;
        const amountMax = parseFloat($('#deducted_amount_max').val()) || Infinity;
        const status = $('#validation_status').val();
        const fromDate = $('#deduction_date_from').val() ? new Date($('#deduction_date_from').val()) : null;
        const toDate = $('#deduction_date_to').val() ? new Date($('#deduction_date_to').val()) : null;

        // Get table data
        const tableCustomer = data[1].toLowerCase(); // Adjust index based on column order
        const tableAmount = parseFloat(data[2].replace(/[^0-9.-]+/g,"")) || 0;
        const tableStatus = data[3];
        let tableDate = null;
        try {
            tableDate = data[4] ? new Date(data[4]) : null;
        } catch(e) {
            console.warn('Invalid date:', data[4]);
            return false;
        }

        // Apply filters with improved matching
        if (customer && !tableCustomer.includes(customer)) return false;
        if (tableAmount < amountMin || tableAmount > amountMax) return false;
        if (status && status !== tableStatus) return false;
        if (fromDate && tableDate && tableDate < fromDate) return false;
        if (toDate && tableDate && tableDate > toDate) return false;

        return true;
    });

    // Initialize Daily Transactions Chart
   $(document).ready(function () {
        console.log("Fetching Daily Transactions Chart data...");

        $.getJSON('/api/daily-transactions/', function (response) {
            const { dates, transactions } = response;

            const chartCanvas = document.getElementById('dailyTransactionsChart');
            if (!chartCanvas) {
                console.error("Canvas element not found!");
                return;
            }

            const ctxDaily = chartCanvas.getContext('2d');

            // Create a target array of 25s (same length as number of dates)
            const targetLine = new Array(dates.length).fill(25);

            window.dailyTransactionsChart = new Chart(ctxDaily, {
                type: 'bar',
                data: {
                    labels: dates,
                    datasets: [{
                        label: 'Transactions Worked',
                        data: transactions,
                        backgroundColor: 'rgba(7, 78, 122, 0.5)',
                        borderColor: 'rgb(15, 93, 145)',
                        borderWidth: 1
                    },
                    {
                        label: 'Target (25)',
                        type: 'line',
                        data: targetLine,  // Same length as labels
                        borderColor: 'rgba(255, 99, 132, 0.8)',
                        borderWidth: 2,
                        pointRadius: 0,
                        fill: false,
                        borderDash: [6, 6],
                    }
                ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                stepSize: 1
                            }
                        }
                    }
                }
            });
        }).fail(function () {
            console.error("Failed to load daily transactions data");
        });
    });



    // Initialize Donut Chart only if not already defined
    if (!window.donutChart) {
        const ctxDonut = document.getElementById('topCustomersDonutChart').getContext('2d');
        window.donutChart = new Chart(ctxDonut, {
            type: 'doughnut',
            data: {
                labels: [],
                datasets: [{
                    data: [],
                    backgroundColor: [
                        '#0d6efd', '#6f42c1', '#d63384', '#dc3545', '#fd7e14',
                        '#ffc107', '#198754', '#20c997', '#0dcaf0', '#6c757d'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            boxWidth: 12,
                            padding: 10
                        }
                    }
                }
            }
        });
    }

   
   

    // Update charts and cards with data from the server
    function updateChartsAndCards(data) {
        // === DONUT CHART UPDATE ===
        if (data.donut_chart_data && data.donut_chart_data.labels && data.donut_chart_data.data) {
            window.donutChart.data.labels = data.donut_chart_data.labels;
            window.donutChart.data.datasets[0].data = data.donut_chart_data.data;
            window.donutChart.update();
        } else {
            console.warn('Donut chart data is missing or incomplete:', data.donut_chart_data);
        }

        // === DAILY TRANSACTIONS CHART UPDATE ===
        if (data.daily_transactions && data.daily_transactions.dates && data.daily_transactions.transactions) {
            if (window.dailyTransactionsChart) {
                window.dailyTransactionsChart.data.labels = data.daily_transactions.dates;
                window.dailyTransactionsChart.data.datasets[0].data = data.daily_transactions.transactions;
                window.dailyTransactionsChart.update();
            } else {
                console.warn("dailyTransactionsChart is not initialized.");
            }
        } else {
            console.warn('Daily transactions chart data is missing or incomplete:', data.daily_transactions);
        }

        // === CARDS UPDATE ===
        if (data.card_data) {
            $('#my-deductions').text(`$${(data.card_data.deductions || 0).toLocaleString()}`);
            $('#my-valids').text(`$${(data.card_data.valids || 0).toLocaleString()}`);
            $('#my-invalids').text(`$${(data.card_data.invalids || 0).toLocaleString()}`);
            $('#my-recovery').text(`$${(data.card_data.recovered || 0).toLocaleString()}`);
        } else {
            console.warn('Card data is missing.');
        }
    }


    // Function to update card values dynamically
    function updateCards(cardData) {
        $('#my-deductions').text(`$${cardData.deductions.toLocaleString()}`);
        $('#my-valids').text(`$${cardData.valids.toLocaleString()}`);
        $('#my-invalids').text(`$${cardData.invalids.toLocaleString()}`);
        $('#my-recovery').text(`$${cardData.recovered.toLocaleString()}`);
    }


    // Modify applyFilters to fetch and update card data
    function applyFilters() {
        $.ajax({
            url: '/filtered-chart-data/',
            type: 'GET',
            data: {
                standard_customer: $('#standard_customer').val(),
                validation_status: $('#validation_status').val(),
                deduction_date_from: $('#deduction_date_from').val(),
                deduction_date_to: $('#deduction_date_to').val(),
                deducted_amount_min: $('#deducted_amount_min').val(),
                deducted_amount_max: $('#deducted_amount_max').val()
            },
            success: function(response) {
                // Update cards with the new data
                updateCards(response.card_data);
                updateChartsAndCards(response);
                table.draw();
                
            },
            error: function(xhr) {
                console.error('Error fetching filtered data:', xhr);
            }
        });
    }

    // Fetch filtered data and update charts/cards
    function fetchFilteredData() {
        const params = new URLSearchParams($('#filter-form').serialize());
        fetch(`/filtered-chart-data/?${params}`)
            .then(response => response.json())
            .then(data => {
                updateChartsAndCards(data);
            })
            .catch(error => console.error('Error fetching filtered data:', error));
    }

    // Fetch initial data and update charts/cards on page load
    function fetchInitialData() {
        fetch('/filtered-chart-data/')
            .then(response => response.json())
            .then(data => {
                updateChartsAndCards(data);
            })
            .catch(error => console.error('Error fetching initial data:', error));
    }
    

    // Call fetchInitialData on page load
    $(document).ready(function() {
        fetchInitialData();
    });

    // Attach fetchFilteredData to filter form submission
    $('#filter-form').on('submit', function(e) {
        e.preventDefault();
        fetchFilteredData();
    });

    
    // Attach fetchFilteredData to the filter button click event
    $('#filter-button').on('click', function(e) {
        e.preventDefault();
        fetchFilteredData();
    });

    // Initialize tooltips for better UX
    $('[data-toggle="tooltip"]').tooltip();

    // Ensure proper column alignment and redraw table on window resize
    $(window).on('resize', function() {
        table.columns.adjust();
    });

    // Ensure proper column alignment after table initialization and on page load
    $(window).on('load', function() {
         
        setTimeout(function() {
            table.columns.adjust();
        }, 100); // Delay to ensure all elements are fully rendered
    });
});









