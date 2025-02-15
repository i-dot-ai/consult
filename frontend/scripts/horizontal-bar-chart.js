class HorizontalBarChart extends HTMLElement {
  constructor() {
      super();
      // Attach a shadow root to the element.
      this.attachShadow({ mode: 'open' });
  }

  connectedCallback() {
      // Create a canvas element.
      const canvas = document.createElement('canvas');
      this.shadowRoot.appendChild(canvas);

      // Get the context of the canvas.
      const ctx = canvas.getContext('2d');

      // Get the data from the attribute.
      const data = JSON.parse(this.getAttribute('data')) || {};
      const labels = Object.keys(data);
      const counts = Object.values(data);

      // Get the data format from the attribute - either 'raw' or 'percentage'.
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

      // Create the chart.
      new Chart(ctx, {
          type: 'bar',
          data: chartData,
          options: chartOptions,
          plugins: [ChartDataLabels]
      });
  }
}

// Define the new element.
customElements.define('horizontal-bar-chart', HorizontalBarChart);
