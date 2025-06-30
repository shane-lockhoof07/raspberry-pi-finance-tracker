<!-- BarChart.vue -->
<template>
    <div :style="{ height: height }" class="chart-container">
      <v-chart
        ref="chart"
        :key="chartKey"
        class="chart"
        :option="chartOption"
        autoresize
      />
    </div>
  </template>
  
  <script>
  // Import ECharts and Vue ECharts
  import * as echarts from 'echarts'
  import VChart from 'vue-echarts'
  
  export default {
    name: 'BarChartComponent',
    components: {
      VChart
    },
    props: {
      data: {
        type: Array,
        required: true,
        validator: (value) => Array.isArray(value)
      },
      categoryField: {
        type: String,
        required: true
      },
      valueFields: {
        type: Array,
        required: true,
        validator: (value) => Array.isArray(value)
      },
      seriesNames: {
        type: Array,
        default: () => []
      },
      title: {
        type: String,
        default: ''
      },
      subtitle: {
        type: String,
        default: ''
      },
      height: {
        type: String,
        default: '400px'
      },
      horizontal: {
        type: Boolean,
        default: false
      },
      colors: {
        type: Array,
        default: () => []
      },
      legendTextColor: {
        type: String,
        default: '#FFFFFF'
      }
    },
    data() {
      return {
        chartKey: 0 // Used to force re-render when data changes
      }
    },
    computed: {
      chartOption() {
        const categories = this.data.map(item => item[this.categoryField]);
        
        // Create the bar series - one for each value field
        const series = this.valueFields.map((field, index) => {
          return {
            name: this.seriesNames[index] || field,
            type: 'bar',
            barGap: '30%', // Gap between bars in the same category
            data: this.data.map(item => item[field]),
            itemStyle: this.colors[index] ? { color: this.colors[index] } : undefined
          }
        });
        
        return {
          tooltip: {
            trigger: 'axis',
            axisPointer: {
              type: 'shadow'
            },
            formatter: function(params) {
              if (params.length === 0) return '';
              
              let result = `${params[0].name}<br/>`;
              params.forEach(param => {
                // Format as currency with $ sign and no decimal places
                const formattedValue = new Intl.NumberFormat('en-US', {
                  style: 'currency',
                  currency: 'USD',
                  minimumFractionDigits: 0,
                  maximumFractionDigits: 0
                }).format(param.value);
                
                result += `${param.seriesName}: ${formattedValue}<br/>`;
              });
              return result;
            }
          },
          legend: {
            data: this.valueFields.map((field, index) => this.seriesNames[index] || field),
            textStyle: {
              color: this.legendTextColor || '#333333'
            }
          },
          grid: {
            left: '3%',
            right: '4%',
            bottom: '3%',
            containLabel: true
          },
          [this.horizontal ? 'yAxis' : 'xAxis']: {
            type: 'category',
            data: categories,
            axisLabel: {
              interval: 0,
              rotate: this.horizontal ? 0 : categories.length > 10 ? 45 : 0
            }
          },
          [this.horizontal ? 'xAxis' : 'yAxis']: {
            type: 'value',
            axisLabel: {
              formatter: function(value) {
                return '$' + value;
              }
            }
          },
          series
        }
      }
    },
    watch: {
      data: {
        handler() {
          this.chartKey += 1 // Force re-render when data changes
        },
        deep: true
      }
    }
  }
  </script>
  
  <style scoped>
  .chart-container {
    width: 100%;
    min-height: 300px;
  }
  
  .chart {
    height: 100%;
    width: 100%;
  }
  </style>