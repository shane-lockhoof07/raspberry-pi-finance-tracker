<template>
    <div class="chart-container" :style="{ height }">
      <div ref="chart" class="chart"></div>
    </div>
  </template>
  
  <script>
  import * as echarts from 'echarts';
  
  export default {
    name: 'BaseLineChart',
    props: {
      data: {
        type: Array,
        required: true
      },
      xField: {
        type: String,
        required: true
      },
      series: {
        type: Array,
        required: true
      },
      colors: {
        type: Array,
        default: () => ['#74b9ff', '#55efc4', '#ff7675', '#a29bfe', '#fab1a0', '#81ecec', '#ffeaa7', '#dfe6e9']
      },
      height: {
        type: String,
        default: '400px'
      },
      title: {
        type: String,
        default: ''
      },
      xAxisName: {
        type: String,
        default: ''
      },
      yAxisName: {
        type: String,
        default: ''
      },
      formatYAxis: {
        type: Function,
        default: value => value
      }
    },
    data() {
      return {
        chart: null
      };
    },
    mounted() {
      this.initChart();
      window.addEventListener('resize', this.resizeChart);
    },
    beforeUnmount() {
      window.removeEventListener('resize', this.resizeChart);
      if (this.chart) {
        this.chart.dispose();
      }
    },
    methods: {
      initChart() {
        this.chart = echarts.init(this.$refs.chart);
        this.updateChart();
      },
      resizeChart() {
        if (this.chart) {
          this.chart.resize();
        }
      },
      updateChart() {
        if (!this.chart) return;
  
        const xAxisData = this.data.map(item => item[this.xField]);
        
        const seriesData = this.series.map((serie, index) => {
          return {
            name: serie.name,
            type: 'line',
            data: this.data.map(item => item[serie.field]),
            smooth: true,
            lineStyle: {
              width: 3
            },
            emphasis: {
              focus: 'series',
              lineStyle: {
                width: 5
              }
            },
            itemStyle: {
              color: this.colors[index % this.colors.length]
            }
          };
        });
  
        const option = {
          title: {
            text: this.title,
            left: 'center',
            textStyle: {
              color: '#FFFFFF'
            }
          },
          tooltip: {
            trigger: 'axis',
            formatter: (params) => {
              let tooltip = `<div style="font-weight: bold; margin-bottom: 5px;">Year: ${params[0].name}</div>`;
              
              // Sort params by value to keep consistent order
              params.sort((a, b) => b.value - a.value);
              
              params.forEach(param => {
                // Make the hovered series bold
                const isBold = param.seriesIndex === params[0].seriesIndex;
                const style = isBold ? 'font-weight: bold;' : '';
                
                // Color marker
                const colorSpan = `<span style="display:inline-block;margin-right:5px;border-radius:50%;width:10px;height:10px;background-color:${param.color};"></span>`;
                
                tooltip += `<div style="${style}padding: 3px 0">${colorSpan}${param.seriesName}: ${this.formatYAxis(param.value)}</div>`;
              });
              
              return tooltip;
            },
            backgroundColor: 'rgba(50,50,50,0.9)',
            borderColor: '#333',
            textStyle: {
              color: '#fff'
            }
          },
          legend: {
            data: this.series.map(serie => serie.name),
            bottom: 0,
            textStyle: {
              color: '#FFFFFF'
            }
          },
          grid: {
            left: '3%',
            right: '4%',
            bottom: '10%',
            top: '10%',
            containLabel: true
          },
          xAxis: {
            type: 'category',
            boundaryGap: true,
            data: xAxisData,
            name: '',
            nameLocation: 'middle',
            nameGap: 30,
            nameTextStyle: {
              color: '#FFFFFF'
            },
            axisLabel: {
              color: '#FFFFFF'
            },
            axisLine: {
              lineStyle: {
                color: '#FFFFFF'
              }
            }
          },
          yAxis: {
            type: 'value',
            name: '',
            nameLocation: 'middle',
            nameGap: 50,
            nameTextStyle: {
              color: '#FFFFFF'
            },
            axisLabel: {
              formatter: this.formatYAxis,
              color: '#FFFFFF'
            },
            axisLine: {
              lineStyle: {
                color: '#FFFFFF'
              }
            }
          },
          series: seriesData
        };
  
        this.chart.setOption(option);
      }
    },
    watch: {
      data: {
        handler() {
          this.updateChart();
        },
        deep: true
      },
      series: {
        handler() {
          this.updateChart();
        },
        deep: true
      }
    }
  };
  </script>
  
  <style scoped>
  .chart-container {
    width: 100%;
    position: relative;
  }
  
  .chart {
    width: 100%;
    height: 100%;
  }
  </style>