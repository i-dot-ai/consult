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
          borderWidth: 1,
          backgroundColor: [
            '#005abb',
            '#a23138',
            '#cc5a13'
          ]
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: {
            display: chart.dataset.legend === 'true'
          }
        }
      }
    });

  });

})();


// Prevalent themes chart
(() => {

  const chart = document.getElementById('prevalent-themes');

  // @ts-ignore
  new Chart(chart, {
    type: 'bar',
    data: {
      labels: [
        'Preventing smoking-related illnesses starts now',
        'Vaping is becoming increasingly popular among young people who have never smoked as they perceive it as a safer alternative to smoking.',
        'Limit children\'s access to tobacco products',
        'Strong public opposition to change in tobacco sale age',
        'Legalise ban on tobacco products for current and future generations',
        'Age of sale for tobacco products should be changed to eradicate smoking',
        'Smoking is harmful and should not be legally sold to anyone born after 1 January 2009',
        'Vaping and smoking both need to be completely unavailable',
        'Protect future generations from the harmful effects of smoking',
        'The majority of respondents support raising the legal age of sale for tobacco products to 18 years old in the UK, believing it will help prevent addiction and reduce peer pressure among young people'
      ],
      datasets: [{
        data: [671, 443, 163, 136, 127, 112, 105, 91, 84, 81]
      }]
    },
    options: {
      indexAxis: 'y',
      // Elements options apply to all of the options unless overridden in a dataset
      // In this case, we are setting the border of each horizontal bar to be 2px wide
      elements: {
        bar: {
          borderWidth: 2,
        }
      },
      responsive: true,
      plugins: {
        legend: {
          display: false
        }
      }
    }
  });

})();