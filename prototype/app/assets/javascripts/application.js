// @ts-check


// Doughnut charts
(() => {

  /** @type {NodeListOf<HTMLCanvasElement>} */
  const doughnutCharts = document.querySelectorAll('[data-yes]');
  let chartObjects = [];

  doughnutCharts.forEach((chart) => {

    let options = {
      responsive: true,
      plugins: {
        legend: {
          display: chart.dataset.legend === 'true'
        }
      }
    };
    if (chart.dataset.labels) {
      options.plugins.datalabels = {
        display: true,
        color: '#FFF',
        formatter: (value, context) => {
            if (value < 10) {
                return '';
            }
            return context.chart.data.labels[context.dataIndex];
            //return `${context.chart.data.labels[context.dataIndex]}\n${value}%`;
        },
        font: {
            size: 14,
            weight: 'bold',
            lineHeight: 1.5
        },
        textAlign: 'center'
      };
    }

    // @ts-ignore
    chartObjects.push(new Chart(chart, {
      type: 'doughnut',
      // @ts-ignore
      plugins: chart.dataset.labels ? [ChartDataLabels]: [],
      data: {
        labels: ['Agree', 'Disagree', 'Not sure'],
        datasets: [{
          data: [chart.dataset.yes, chart.dataset.no, 100 - parseInt(chart.dataset.yes || '0') - parseInt(chart.dataset.no || '0')],
          borderWidth: 1,
          backgroundColor: [ // based on https://analysisfunction.civilservice.gov.uk/policy-store/data-visualisation-colours-in-charts/
            '#12436D',
            '#801650',
            '#F46A25'
          ]
        }]
      },
      options: options
    }));

  });

  // Trigger chart animation when a tab containing a chart is activated
  document.querySelector('#tab_findings')?.addEventListener('click', () => {
    chartObjects.forEach((chart) => {
      chart.reset();
      chart.update();
    });
  });

})();


// Prevalent themes bars animation
(() => {

  /** @type {NodeListOf<HTMLElement>} */
  const bars = document.querySelectorAll('.js-bar');
  bars.forEach((bar) => {
    const originalWidth = bar.style.width;
    bar.style.width = '0%';
    window.setTimeout(() => {
      bar.classList.add('animate');
      bar.style.width = originalWidth;
    }, 1);
  });

})();
