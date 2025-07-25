//@ts-check


// donut chart
class DonutChart extends HTMLElement {
    connectedCallback() {

        // pull in data
        /** @type {NodeListOf<HTMLElement>} */
        const items = this.querySelectorAll('chart-item');
        let data = [];
        items.forEach((item) => {
            data.push({
                name: item.dataset.label,
                value: item.dataset.count
            });
        });

        /**
         * Size the chart and chart container
         * @param {boolean} firstTime
         */
        const sizeChart = (firstTime) => {
            this.style.display = 'none';
            this.style.width = `${this.parentElement?.scrollWidth}px`;
            this.style.height = `${this.parentElement?.scrollWidth}px`;
            this.style.display = 'block';
            if (!firstTime) {
                const box = this.getBoundingClientRect();
                chart.resize({
                    height: box.width,
                    width: box.height
                });
            }
        };
        sizeChart(true);

        // setup chart
        // @ts-ignore (echarts global)
        let chart = echarts.init(this, null, {renderer: 'svg'});
        const options = {
            color: [
                '#12436D',
                '#28A197',
                '#801650',
                '#F46A25',
                '#3D3D3D',
                '#A285D1'
            ],
            tooltip: {
                formatter: '{b} ({c}%)',
                trigger: 'item'
            },
            grid: {
                left: 0,
                top: 0,
                right: 0,
                bottom: 0
            },
            series: [
                {
                    type: 'pie',
                    radius: ['40%', '90%'],
                    itemStyle: {
                        borderColor: '#fff',
                        borderWidth: 1
                    },
                    data: data,
                    label: {
                        align: 'left',
                        color: '#fff',
                        fontSize: 14,
                        fontWeight: 'bold',
                        formatter: [
                            //'{b}',
                            //'\n{percent|{c}%}'
                            '{c}%'
                        ].join('\n'),
                        lineHeight: 14,
                        position: 'inside',
                        width: 70,
                        overflow: 'break',
                        rich: {
                            percent: {
                                lineHeight: 18,
                                fontWeight: 'normal'
                            }
                        }
                    }
                }
            ]
        };
        chart.setOption(options);
        window.addEventListener('resize', () => {
            sizeChart(false);
        });

    }
}
customElements.define('donut-chart', DonutChart);



class BarAnimation extends HTMLElement {
    connectedCallback () {

        // check user hasn't requested reduced motion
        if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
            return;
        }

        const bar = this.querySelector('span');
        if (!bar) {
            return;
        }
        const originalWidth = bar.style.width;
        bar.style.width = '0%';
        window.setTimeout(() => {
            bar.classList.add('animate');
            bar.style.width = originalWidth;
        }, 1);

    }
}
customElements.define('bar-animation', BarAnimation);
