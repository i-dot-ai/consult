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



// Prevalent themes chart
/*
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
*/


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