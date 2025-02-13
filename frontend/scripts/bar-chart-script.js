document.addEventListener('DOMContentLoaded', function() {
  const questions = {{ questions | dump | safe }};
  const multipleChoiceCounts = {{ multipleChoiceCounts | dump | safe }};


  questions.forEach(question => {
    if (question.multiple_choice) {
      const labels = question.multiple_choice.options;
      const data = labels.map(label => multipleChoiceCounts[question.id][label] || 0);

      new Chart(document.getElementById(`chart-${question.id}`), {
        type: 'bar',
        data: {
          labels: labels,
          datasets: [{
            label: question.multiple_choice.question_text,
            data: data,
            backgroundColor: ['#003c57'],
            hoverOffset: 4
          }]
        },
        options: {
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
                const datapoints = ctx.chart.data.datasets[0].data;
                const total = datapoints.reduce((total, datapoint) => total + datapoint, 0);
                const percentage = value / total * 100;
                return percentage.toFixed(0) + "%";
              }
            }
          }
        },
        plugins: [ChartDataLabels]
      });
    }
  });
});

