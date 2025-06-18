// Chart instances
let quarterlyTrendChart = null;
let quarterlyDeductionsChart = null;
let toleranceChart = null;
let reasonsChart = null;

// Store chart instances for horizontal bar charts
let deductionBreakdownChart = null;
let deductionPercentageChart = null;
let invalidPercentageChart = null;
let recoveryPercentageChart = null;

// Store chart instances for top customerhorizontal bar charts
let topCustomersBreakdownChart = null;
let topCustomersPercentageChart = null;
let topCustomersInvalidChart = null;
let topCustomersRecoveryChart = null;

// Utility functions
function formatCurrency(value) {
    const amount = parseFloat(value) || 0;
    return '$' + amount.toLocaleString(undefined, {
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    });
}

// Generate and store dummy values for recovery percentages
const recoveryDummyValues = []; // Ensure dummy values are generated only once

// Initialize Charts
function initializeCharts() {
    // Create chart contexts
    const trendCtx = document.getElementById('quarterlyTrendChart')?.getContext('2d');
    const deductionsCtx = document.getElementById('openclosedChart')?.getContext('2d');
    const toleranceCtx = document.getElementById('toleranceChart')?.getContext('2d');
    const reasonsCtx = document.getElementById('reasonsChart')?.getContext('2d');

    if (!trendCtx || !deductionsCtx || !toleranceCtx || !reasonsCtx) {
        console.error('Could not get all chart contexts');
        return;
    }

    // Quarterly Trend Chart
    quarterlyTrendChart = new Chart(trendCtx, {
        type: 'line',
        data: {
            labels: window.quarters,
            datasets: [{
                label: 'Total Deductions',
                data: window.openAmounts.map((open, i) => 
                    parseFloat(open || 0) + parseFloat(window.closedAmounts[i] || 0)
                ),
                borderColor: '#0d6efd',
                backgroundColor: 'rgba(13, 110, 253, 0.1)',
                fill: true,
                tension: 0.4,
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: value => formatCurrency(value)
                    }
                }
            }
        }
    });

    // Open/Closed Distribution Chart
    quarterlyDeductionsChart = new Chart(deductionsCtx, {
        type: 'bar',
        data: {
            labels: window.quarters,
            datasets: [
                {
                    label: 'Open',
                    data: window.openAmounts.map(v => parseFloat(v) || 0),
                    backgroundColor: '#ffc107',
                    borderWidth: 1
                },
                {
                    label: 'Closed',
                    data: window.closedAmounts.map(v => parseFloat(v) || 0),
                    backgroundColor: '#198754',
                    borderWidth: 1
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
                        callback: value => formatCurrency(value)
                    }
                }
            }
        }
    });

    // Parse tolerance data
    const toleranceData = typeof window.toleranceData === 'string' ? 
        JSON.parse(window.toleranceData) : window.toleranceData;

    // Tolerance Chart
    toleranceChart = new Chart(toleranceCtx, {
        type: 'bar',
        data: {
            labels: toleranceData.labels || [],
            datasets: [
                {
                    label: 'Under Tolerance',
                    data: (toleranceData.ut_data || []).map(v => parseFloat(v) || 0),
                    backgroundColor: '#ffc107',
                    borderColor: '#ffc107',
                    borderWidth: 1
                },
                {
                    label: 'Over Tolerance',
                    data: (toleranceData.ot_data || []).map(v => parseFloat(v) || 0),
                    backgroundColor: '#dc3545',
                    borderColor: '#dc3545',
                    borderWidth: 1
                }
            ]
        },
        options: {
            indexAxis: 'x',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'right',
                    labels: {
                        boxWidth: 12,
                        padding: 10,
                        usePointStyle: true,
                        font: {
                            size: 11
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: value => formatCurrency(value)
                    }
                }
            }
        }
    });

    // Parse reason data
    const reasonData = typeof window.reasonChartData === 'string' ? 
        JSON.parse(window.reasonChartData) : window.reasonChartData;

    // Reasons Chart
    reasonsChart = new Chart(reasonsCtx, {
        type: 'doughnut',
        data: {
            labels: reasonData.labels || [],
            datasets: [{
                data: (reasonData.data || []).map(v => parseFloat(v) || 0),
                backgroundColor: [
                   '#0d6efd', '#6f42c1', '#d63384', '#dc3545', '#fd7e14',
                   '#ffc107', '#198754', '#20c997', '#0dcaf0', '#6c757d'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'right',
                    align: 'center',
                    labels: {
                        boxWidth: 12,
                        padding: 10,
                        usePointStyle: true,
                        font: {
                            size: 11
                        }
                    }
                }
            },
            layout: {
                padding: {
                    left: 10,
                    right: 120  // Add padding to accommodate the legend
                }
            }
        }
    });
}

// Initialize Horizontal Bar Charts
function initializeHorizontalBarCharts(reasonChartData, totalsData) {
    if (!reasonChartData || !reasonChartData.labels || !reasonChartData.data || !reasonChartData.invalid_data || !reasonChartData.recovery_data) {
        console.error('Invalid or missing reasonChartData:', reasonChartData);
        return;
    }

    const breakdownCtx = document.getElementById('deductionBreakdownChart')?.getContext('2d');
    const percentageCtx = document.getElementById('deductionPercentageChart')?.getContext('2d');
    const invalidCtx = document.getElementById('invalidPercentageChart')?.getContext('2d');
    const recoveryCtx = document.getElementById('recoveryPercentageChart')?.getContext('2d');

    if (!breakdownCtx || !percentageCtx || !invalidCtx || !recoveryCtx) {
        console.error('Could not get all horizontal bar chart contexts');
        return;
    }

    const labels = reasonChartData.labels;
    const deductionAmounts = reasonChartData.data;
    const invalidAmounts = reasonChartData.invalid_data;
    const recoveryPercentages = reasonChartData.recovery_data;
    const totalRevenue = totalsData.total_revenue || 1; // Avoid division by zero

    // Destroy existing chart instances if they exist
    if (deductionBreakdownChart) deductionBreakdownChart.destroy();
    if (deductionPercentageChart) deductionPercentageChart.destroy();
    if (invalidPercentageChart) invalidPercentageChart.destroy();
    if (recoveryPercentageChart) recoveryPercentageChart.destroy();

    const colors = [
        '#0d6efd', '#6f42c1', '#d63384', '#dc3545', '#fd7e14',
        '#ffc107', '#198754', '#20c997', '#0dcaf0', '#6c757d'
    ];

    // Deduction Breakdown Chart
    deductionBreakdownChart = new Chart(breakdownCtx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Deduction Amount ($)',
                data: deductionAmounts,
                backgroundColor: colors,
                borderColor: colors,
                borderWidth: 1
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: { callbacks: { label: context => `$${context.raw}` } }
            },
            scales: {
                x: { beginAtZero: true },
                y: { beginAtZero: true }
            }
        }
    });

    // Deduction Percentage Chart
    deductionPercentageChart = new Chart(percentageCtx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Deduction % of Revenue',
                data: deductionAmounts.map(amount => ((amount / totalRevenue) * 100).toFixed(2)),
                backgroundColor: colors,
                borderColor: colors,
                borderWidth: 1
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: { callbacks: { label: context => `${context.raw}%` } }
            },
            scales: {
                x: { display: true },
                y: { display: false }
            }
        }
    });

    // Invalid Percentage Chart
    invalidPercentageChart = new Chart(invalidCtx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Invalid % of Deductions',
                data: deductionAmounts.map((amount, index) => {
                    const invalidAmount = invalidAmounts[index] || 0;
                    return ((invalidAmount / amount) * 100).toFixed(2);
                }),
                backgroundColor: colors,
                borderColor: colors,
                borderWidth: 1
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: { callbacks: { label: context => `${context.raw}%` } }
            },
            scales: {
                x: { display: true },
                y: { display: false }
            }
        }
    });

    // Recovery Percentage Chart
    recoveryPercentageChart = new Chart(recoveryCtx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Recovery % of Invalids',
                data: recoveryPercentages,
                backgroundColor: colors,
                borderColor: colors,
                borderWidth: 1
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: { callbacks: { label: context => `${context.raw}%` } }
            },
            scales: {
                x: { display: true },
                y: { display: false }
            }
        }
    });
}

// Initialize Customer Horizontal Bar Charts
function initializeCustomerHorizontalBarCharts(customerChartData, totalsData) {
    if (!customerChartData || !customerChartData.labels || !customerChartData.data || !customerChartData.invalid_data || !customerChartData.recovery_data) {
        console.error('Invalid or missing customerChartData:', customerChartData);
        return;
    }

    const topcustomersbreakdownCtx = document.getElementById('topCustomersBreakdownChart')?.getContext('2d');
    const topcustomerspercentageCtx = document.getElementById('topCustomersPercentageChart')?.getContext('2d');
    const topcustomersinvalidCtx = document.getElementById('topCustomersInvalidChart')?.getContext('2d');
    const topcustomersrecoveryCtx = document.getElementById('topCustomersRecoveryChart')?.getContext('2d');

    if (!topcustomersbreakdownCtx || !topcustomerspercentageCtx || !topcustomersinvalidCtx || !topcustomersrecoveryCtx) {
        console.error('Could not get all customer horizontal bar chart contexts');
        return;
    }

    const toplabels = customerChartData.labels;
    const topdeductionAmounts = customerChartData.data;
    const topinvalidAmounts = customerChartData.invalid_data;
    const toprecoveryPercentages = customerChartData.recovery_data;
    const totalRevenue = totalsData.total_revenue || 1; // Avoid division by zero

    // Destroy existing chart instances if they exist
    if (topCustomersBreakdownChart) topCustomersBreakdownChart.destroy();
    if (topCustomersPercentageChart) topCustomersPercentageChart.destroy();
    if (topCustomersInvalidChart) topCustomersInvalidChart.destroy();
    if (topCustomersRecoveryChart) topCustomersRecoveryChart.destroy();

    const topCustomerColors = [
        '#ff5733', '#0a7a1b', '#3357ff', '#ff33a1', '#a133ff',
        '#0a6f7a', '#abad0a', '#ff8c33', '#ad0a43', '#338cff'
    ];

    // Deduction Breakdown Chart
    topCustomersBreakdownChart = new Chart(topcustomersbreakdownCtx, {
        type: 'bar',
        data: {
            labels: toplabels,
            datasets: [{
                label: 'Deduction Amount ($)',
                data: topdeductionAmounts,
                backgroundColor: topCustomerColors,
                borderColor: topCustomerColors,
                borderWidth: 1
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: { callbacks: { label: context => `$${context.raw}` } }
            },
            scales: {
                x: { beginAtZero: true },
                y: { beginAtZero: true }
            }
        }
    });

    // Deduction Percentage Chart
    topCustomersPercentageChart = new Chart(topcustomerspercentageCtx, {
        type: 'bar',
        data: {
            labels: toplabels,
            datasets: [{
                label: 'Deduction % of Revenue',
                data: topdeductionAmounts.map(amount => ((amount / totalRevenue) * 100).toFixed(2)),
                backgroundColor: topCustomerColors,
                borderColor: topCustomerColors,
                borderWidth: 1
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: { callbacks: { label: context => `${context.raw}%` } }
            },
            scales: {
                x: { display: true },
                y: { display: false }
            }
        }
    });

    // Invalid Percentage Chart
    topCustomersInvalidChart = new Chart(topcustomersinvalidCtx, {
        type: 'bar',
        data: {
            labels: toplabels,
            datasets: [{
                label: 'Invalid % of Deductions',
                data: topdeductionAmounts.map((amount, index) => {
                    const invalidAmount = topinvalidAmounts[index] || 0;
                    return ((invalidAmount / amount) * 100).toFixed(2);
                }),
                backgroundColor: topCustomerColors,
                borderColor: topCustomerColors,
                borderWidth: 1
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: { callbacks: { label: context => `${context.raw}%` } }
            },
            scales: {
                x: { display: true },
                y: { display: false }
            }
        }
    });

    // Recovery Percentage Chart
    topCustomersRecoveryChart = new Chart(topcustomersrecoveryCtx, {
        type: 'bar',
        data: {
            labels: toplabels,
            datasets: [{
                label: 'Recovery % of Invalids',
                data: toprecoveryPercentages,
                backgroundColor: topCustomerColors,
                borderColor: topCustomerColors,
                borderWidth: 1
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: { callbacks: { label: context => `${context.raw}%` } }
            },
            scales: {
                x: { display: true },
                y: { display: false }
            }
        }
    });
}

// Update Horizontal Bar Charts with Data
function updateHorizontalBarCharts(data) {
    const reasonChartData = data.reason_chart_data || {};
    const totalsData = data.totals || {};
    initializeHorizontalBarCharts(reasonChartData, totalsData);
}

// Function to reset all charts to original window data
function resetAllData() {
    // Reset form
    $('#filter-form')[0].reset();    // Make AJAX request to get initial data
    fetch('/insights/', {
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            updateChartsWithData(data);
            $('#total_revenue').text(formatCurrency(data.totals?.total_revenue || 0));
        })
        .catch(error => {
            console.error('Error fetching initial data:', error);
            if (quarterlyTrendChart) quarterlyTrendChart.destroy();
            if (quarterlyDeductionsChart) quarterlyDeductionsChart.destroy();
            if (toleranceChart) toleranceChart.destroy();
            if (reasonsChart) reasonsChart.destroy();
            initializeCharts();
        });
}

// Update charts with new data, including horizontal bar charts
function updateChartsWithData(data) {
    // Update window data with new data
    window.quarters = data.quarters || data.totals?.quarters || window.quarters;
    window.openAmounts = data.open_amounts || data.totals?.open_amounts || window.openAmounts;
    window.closedAmounts = data.closed_amounts || data.totals?.closed_amounts || window.closedAmounts;
    window.toleranceData = data.tolerance_data || data.totals?.tolerance_data || window.toleranceData;
    window.reasonChartData = data.reason_chart_data || data.totals?.reason_chart_data || window.reasonChartData;
    window.customerChartData = data.customerChartData || data.totals?.customerChartData || window.customerChartData;

    // Update window.totalRevenue with the correct value from the AJAX response
    if (data.totals?.total_revenue) {
        window.totalRevenue = data.totals.total_revenue;
    } else {
        window.totalRevenue = 1; // Fallback value
    }

    // Destroy existing charts
    if (quarterlyTrendChart) quarterlyTrendChart.destroy();
    if (quarterlyDeductionsChart) quarterlyDeductionsChart.destroy();
    if (toleranceChart) toleranceChart.destroy();
    if (reasonsChart) reasonsChart.destroy();


    // Initialize charts with new data
    initializeCharts();

    // Update horizontal bar charts with filtered data
    if (window.reasonChartData && window.reasonChartData.labels) {
        const totalRevenue = window.totalRevenue > 0 ? window.totalRevenue : 1;
        initializeHorizontalBarCharts(window.reasonChartData, { total_revenue: totalRevenue });
    } else {
        console.error('reasonChartData is missing or invalid during update:', window.reasonChartData);
    }

    // Update top customer horizontal bar charts with filtered data
    if (window.customerChartData && window.customerChartData.labels) {
        const totalRevenue = window.totalRevenue > 0 ? window.totalRevenue : 1;
        initializeCustomerHorizontalBarCharts(window.customerChartData, { total_revenue: totalRevenue });
    } else {
        console.error('top customer data is missing or invalid during update:', window.customerChartData);
    }

    // Update revenue card dynamically
    const totalsData = data.totals || {};
    if (totalsData) {
        $('#total_revenue').text(formatCurrency(totalsData.total_revenue));
        $('#ytd_deductions').text(formatCurrency(totalsData.ytd_deductions));
        $('#deductions_percentage').text(totalsData.deductions_percentage + '%');
        $('#total_deductions').text(formatCurrency(totalsData.total_deductions));
        $('#valid_deductions').text(formatCurrency(totalsData.valid_deductions));
        $('#under_tolerance').text(formatCurrency(totalsData.under_tolerance || 0));
        $('#invalid_deductions').text(formatCurrency(totalsData.invalid_deductions));
        $('#pending_deductions').text(formatCurrency(totalsData.pending_deductions));
    }
}

// Function to update charts based on filters
function updateChartsWithFilters(filterCriteria) {
    // Make AJAX request to fetch filtered data
    fetch(`/insights/?${new URLSearchParams(filterCriteria)}`, {
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        // Update all charts with filtered data
        updateChartsWithData(data);

        // Ensure top customer charts are updated with filtered data
        if (data.topcustomer_chart_data && data.topcustomer_chart_data.labels) {
            initializeCustomerHorizontalBarCharts(data.topcustomer_chart_data, { total_revenue: data.totals?.total_revenue || 1 });
        } else {
            console.error('Filtered customer chart data is missing or invalid:', data.topcustomer_chart_data);
        }
    })
    .catch(error => {
        console.error('Error fetching filtered data:', error);
    });
}

// Fetch and update Top 10 Customers charts
function updateTopCustomersCharts(data) {
    if (!data || !data.topcustomer_chart_data) {
        console.error('Customer chart data is missing or undefined:', data);
        return;
    }

    const customerChartData = data.topcustomer_chart_data;
    const totalsData = data.totals || {};

    // Fallback mechanism for missing data
    if (!customerChartData.labels || !customerChartData.data || !customerChartData.invalid_data || !customerChartData.recovery_data) {
        console.warn('Incomplete customer chart data detected, applying fallback values.');
        customerChartData.labels = customerChartData.labels || [];
        customerChartData.data = customerChartData.data || [];
        customerChartData.invalid_data = customerChartData.invalid_data || [];
        customerChartData.recovery_data = customerChartData.recovery_data || [];
    }

    initializeCustomerHorizontalBarCharts(customerChartData, totalsData);
}

// Initialize when document is ready
$(document).ready(function() {
    // Consolidate AJAX call to fetch initial data
    fetch('/insights/', {
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        window.totalRevenue = data.totals?.total_revenue || 1;

        // Initialize all charts with fetched data
        initializeCharts();

        if (data.reason_chart_data && data.reason_chart_data.labels) {
            initializeHorizontalBarCharts(data.reason_chart_data, { total_revenue: window.totalRevenue });
        } else {
            console.error('reasonChartData is missing or invalid during page load:', data.reason_chart_data);
        }

        if (data.topcustomer_chart_data && data.topcustomer_chart_data.labels) {
            initializeCustomerHorizontalBarCharts(data.topcustomer_chart_data, { total_revenue: window.totalRevenue });
        } else {
            console.error('Customer chart data is missing or invalid during page load:', data.topcustomer_chart_data);
        }

        // Update Top Customers charts
        updateTopCustomersCharts(data);
    })
    .catch(error => {
        console.error('Error fetching insights data:', error);
    });

    // Handle form submission for filters
    $('#filter-form').on('submit', function(e) {
        e.preventDefault();

        const formData = new FormData(this);
        const filterCriteria = Object.fromEntries(formData.entries());

        // Fetch and update charts based on filter criteria
        updateChartsWithFilters(filterCriteria);
    });

    // Handle reset button click
    $('#resetInsightsFilters').on('click', function(e) {
        e.preventDefault();
        resetAllData();
    });
});