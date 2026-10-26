// Chart.js options for the warehouse dashboard's throughput, labour, orders and stock charts.

// 1. Throughput Line Chart
export const lineChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: { display: false },
        tooltip: {
            mode: 'index',
            intersect: false,
            backgroundColor: 'rgba(0,0,0,0.8)',
            titleColor: '#fff',
            bodyColor: '#4fd1c5', // teal-400
            borderColor: 'rgba(255,255,255,0.1)',
            borderWidth: 1,
            padding: 10,
            cornerRadius: 8
        }
    },
    scales: {
        y: {
            beginAtZero: true,
            grid: { color: 'rgba(255,255,255,0.05)', drawBorder: false },
            ticks: { color: '#9ca3af', font: { size: 10, family: 'Inter' } }
        },
        x: {
            grid: { display: false, drawBorder: false },
            ticks: { color: '#9ca3af', font: { size: 10, family: 'Inter' } }
        }
    },
    interaction: { mode: 'nearest', axis: 'x', intersect: false }
}

// 2. Labor Doughnut Chart (Bottom Right Widget)
export const doughnutOptions = {
    responsive: true,
    maintainAspectRatio: false,
    cutout: '75%',
    plugins: {
        legend: {
            position: 'bottom',
            labels: {
                color: '#d1d5db',
                usePointStyle: true,
                boxWidth: 8,
                font: { size: 11, family: 'Inter' },
                padding: 15
            }
        },
        tooltip: {
            backgroundColor: 'rgba(0,0,0,0.8)',
            bodyColor: '#fff',
            borderColor: 'rgba(255,255,255,0.1)',
            borderWidth: 1,
            callbacks: {
                label: function (context) {
                    return ` ${context.label}: ${context.raw} Staff`;
                }
            }
        }
    }
}

// 3. Orders vs Returns (Bar Chart)
export const barOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: {
            position: 'bottom',
            labels: { color: '#d1d5db', usePointStyle: true, font: { size: 10, family: 'Inter' } }
        },
        tooltip: {
            backgroundColor: 'rgba(0,0,0,0.8)', titleColor: '#fff',
            borderColor: 'rgba(255,255,255,0.1)', borderWidth: 1, cornerRadius: 8
        }
    },
    scales: {
        y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#9ca3af', font: { size: 10 } } },
        x: { grid: { display: false }, ticks: { color: '#9ca3af', font: { size: 10 } } }
    }
};

// 4. Stock vs Packaging (Pie Chart)
export const pieOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: {
            position: 'right',
            labels: { color: '#d1d5db', usePointStyle: true, font: { size: 11, family: 'Inter' }, padding: 12 }
        },
        tooltip: {
            backgroundColor: 'rgba(0,0,0,0.8)',
            bodyColor: '#fff',
            borderColor: 'rgba(255,255,255,0.1)',
            borderWidth: 1,
            callbacks: { label: (c) => ` ${c.label}: ${c.raw}%` }
        }
    }
};
