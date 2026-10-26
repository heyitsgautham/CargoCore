// Chart.js datasets and options for the vendor tracking analytics tab.
const primaryColor = '#3b82f6' // blue-500

export function spendChart(monthly) {
    return {
        labels: monthly.map(m => m.month),
        datasets: [{
            label: 'Monthly Spend (₹)',
            data: monthly.map(m => m.spend),
            backgroundColor: primaryColor + '40', // 25% opacity
            borderColor: primaryColor,
            borderWidth: 2,
            borderRadius: 4,
            hoverBackgroundColor: primaryColor + '80'
        }]
    }
}

export function volumeChart(monthly) {
    return {
        labels: monthly.map(m => m.month),
        datasets: [{
            label: 'Orders',
            data: monthly.map(m => m.orders),
            borderColor: primaryColor,
            backgroundColor: primaryColor + '20',
            fill: true,
            tension: 0.4,
            pointBackgroundColor: '#ffffff',
            pointBorderColor: primaryColor,
            pointBorderWidth: 2,
            pointRadius: 4,
            pointHoverRadius: 6
        }]
    }
}

export const spendChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: {
      backgroundColor: '#1f2937',
      padding: 10,
      cornerRadius: 4,
      displayColors: false,
      callbacks: {
        label: (context) => `₹${context.raw.toLocaleString()}`
      }
    }
  },
  scales: {
    y: {
      beginAtZero: true,
      grid: { color: 'rgba(156, 163, 175, 0.1)' },
      ticks: {
        callback: (value) => '₹' + (value / 1000) + 'k',
        font: { size: 10 }
      }
    },
    x: {
      grid: { display: false },
      ticks: { font: { size: 10 } }
    }
  }
}

export const volumeChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: { display: false },
        tooltip: {
            backgroundColor: '#1f2937',
            padding: 10,
            displayColors: false
        }
    },
    scales: {
        y: {
            beginAtZero: true,
            grid: { color: 'rgba(156, 163, 175, 0.1)' },
            ticks: { font: { size: 10 } }
        },
        x: {
            grid: { display: false },
            ticks: { font: { size: 10 } }
        }
    }
}
