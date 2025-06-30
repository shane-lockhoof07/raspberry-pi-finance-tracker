<!-- BaseStackedBarChart.vue -->
<template>
    <div :style="{ height: height }" class="chart-container">
      <v-chart
        ref="chart"
        :key="chartKey"
        class="chart"
        :option="chartOption"
        autoresize
        @click="handleChartClick"
      />
    </div>
  </template>
  
  <script>
  // Import ECharts and Vue ECharts
  import * as echarts from 'echarts'
  import VChart from 'vue-echarts'
  
  export default {
    name: 'StackedBarChartComponent',
    components: {
      VChart
    },
    props: {
      data: {
        type: Array,
        required: true,
        default: () => []
      },
      categoryField: {
        type: String,
        required: true
      },
      stackedFields: {
        type: Array,
        default: () => ['spending', 'investments', 'rent']
      },
      stackedNames: {
        type: Array,
        default: () => ['Spending', 'Investments', 'Rent']
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
      stackedColors: {
        type: Array,
        default: () => ['#ff7675', '#74b9ff', '#55efc4'] // Red, Blue, Green
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
        // Ensure data is an array
        const safeData = Array.isArray(this.data) ? this.data : [];
        
        // Extract categories from data
        const categories = safeData.map(item => 
          item && typeof item === 'object' ? (item[this.categoryField] || '') : ''
        );
        
        // Create series for stacked items (spending, investments, rent)
        const stackedSeries = this.stackedFields.map((field, index) => {
          return {
            name: this.stackedNames[index] || field,
            type: 'bar',
            stack: 'total',
            emphasis: {
              focus: 'series'
            },
            data: safeData.map(item => 
              item && typeof item === 'object' ? (item[field] || 0) : 0
            ),
            itemStyle: {
              color: this.stackedColors[index] || undefined
            }
          }
        });
        
        // Combine stacked and income series
        const series = [...stackedSeries];
        
        return {
          tooltip: {
            trigger: 'axis',
            axisPointer: {
              type: 'shadow'
            },
            formatter: (params) => {
              if (params.length === 0) return '';
              
              const category = params[0].name;
              let result = `${category}<br/>`;
              
              // Process stacked items first
              let totalExpenses = 0;
              const stackedItems = params.filter(param => 
                this.stackedFields.includes(param.seriesName.toLowerCase()) || 
                this.stackedNames.includes(param.seriesName)
              );
              
              stackedItems.forEach(param => {
                // Format as currency
                const formattedValue = this.formatCurrency(param.value);
                result += `${param.seriesName}: ${formattedValue}<br/>`;
                totalExpenses += param.value || 0;
              });
              
              // Add total expenses
              if (stackedItems.length > 0) {
                result += `<strong>Total: ${this.formatCurrency(totalExpenses)}</strong><br/>`;
              }
              return result;
            }
          },
          legend: {
            data: [...this.stackedNames],
            textStyle: {
              color: this.legendTextColor
            }
          },
          grid: {
            left: '3%',
            right: '4%',
            bottom: '3%',
            containLabel: true
          },
          xAxis: {
            type: 'category',
            data: categories,
            axisLabel: {
              interval: 0,
              rotate: categories.length > 10 ? 45 : 0
            }
          },
          yAxis: {
            type: 'value',
            axisLabel: {
              formatter: (value) => {
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
        handler(newData) {
          // Add validation
          if (!Array.isArray(newData)) {
            console.warn('StackedBarChart: data prop is not an array', newData);
          }
          this.chartKey += 1; // Force re-render when data changes
        },
        deep: true
      }
    },
    methods: {
      handleChartClick(params) {
        if (params.componentType === 'series') {
          // Get the clicked bar data
          const dataIndex = params.dataIndex;
          const seriesName = params.seriesName;
          const value = params.value;
          const category = params.name;
          
          // Get full data item if valid index
          const item = Array.isArray(this.data) && dataIndex >= 0 && dataIndex < this.data.length 
            ? this.data[dataIndex] 
            : {};
          
          // Emit event with click data
          this.$emit('bar-click', {
            category,
            value,
            seriesName,
            dataIndex,
            fullData: item
          });
        }
      },
      
      formatCurrency(value) {
        return new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: 'USD',
          minimumFractionDigits: 0,
          maximumFractionDigits: 0
        }).format(value || 0);
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