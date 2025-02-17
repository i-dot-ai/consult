//@ts-check

class HorizontalBarChart extends HTMLElement {
  constructor() {
      super();

  }

  connectedCallback() {
      const canvas = document.createElement('canvas');
      this.appendChild(canvas);

      const ctx = canvas.getContext('2d');

      const data = JSON.parse(this.getAttribute('data')) || {};
      const labels = Object.keys(data);
      const counts = Object.values(data);

      // Data format is 'raw' for counts, or 'percentage'.
      const dataFormat = this.getAttribute('data-format') || 'raw';

      // Define the chart data and options.
      const chartData = {
          labels: labels,
          datasets: [{
              label: 'Counts',
              data: counts,
              backgroundColor: ['#003c57'],
              hoverOffset: 4
          }]
      };

      const chartOptions = {
          responsive: true,
          maintainAspectRatio: false,
          indexAxis: 'y',
          scales: {
              x: {
                  display: false,
                  grid: {
                      display: false
                  }
              },
              y: {
                  grid: {
                      display: false
                  },
                  ticks: {
                      color: '#0b0c0c',
                      align: 'center',
                      crossAlign: "far",
                      font: {
                          size: 16
                      }
                  }
              }
          },
          plugins: {
              legend: {
                  display: false
              },
              tooltip: {
                  enabled: false
              },
              datalabels: {
                  color: 'white',
                  font: {
                      size: 12
                  },
                  formatter: (value, ctx) => {
                      if (dataFormat === 'percentage') {
                          const datapoints = ctx.chart.data.datasets[0].data;
                          const total = datapoints.reduce((total, datapoint) => total + datapoint, 0);
                          const percentage = value / total * 100;
                          return percentage.toFixed(0) + "%";
                      } else {
                          return value;
                      }
                  }
              }
          }
      };

      new Chart(ctx, {
          type: 'bar',
          data: chartData,
          options: chartOptions,
          plugins: [ChartDataLabels]
      });
  }
}

customElements.define('horizontal-bar-chart', HorizontalBarChart);
