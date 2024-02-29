// @ts-check


// Key findings charts
(() => {

  /** @type {NodeListOf<HTMLCanvasElement>} */
  const keyFindingCharts = document.querySelectorAll('[data-yes]');

  keyFindingCharts.forEach((chart) => {

    // @ts-ignore
    new Chart(chart, {
      type: 'doughnut',
      data: {
        labels: ['In favour', 'Opposed', 'Undecided'],
        datasets: [{
          data: [chart.dataset.yes, chart.dataset.no, 100 - parseInt(chart.dataset.yes || '0') - parseInt(chart.dataset.no || '0')],
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: {
            display: false
          }
        }
      }
    });

  });

})();
