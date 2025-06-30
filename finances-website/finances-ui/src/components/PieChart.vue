<template>
    <v-container>
      <v-card>
        <v-card-text>
          <div class="chart-container">
            <canvas ref="pieChartCanvas"></canvas>
          </div>
          <div v-if="!hasData" class="text-center pa-4">
            No data available to display
          </div>
        </v-card-text>
      </v-card>
    </v-container>
  </template>
  
  <script>
  import Chart from 'chart.js/auto';
  
  export default {
    name: 'PieChart',
    props: {
      title: {
        type: String,
        default: 'Pie Chart',
      },
      categories: {
        type: Array,
        required: true,
        validator: (value) => Array.isArray(value)
      },
      values: {
        type: Array,
        required: true,
        validator: (value) => Array.isArray(value)
      },
      colors: {
        type: Array,
        default: () => ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF'],
      },
      // Added prop to control chart type
      chartType: {
        type: String,
        default: 'doughnut',
        validator: (value) => ['pie', 'doughnut'].includes(value)
      }
    },
    data() {
      return {
        chartInstance: null,
        clickHandler: null,
        moveHandler: null,
      };
    },
    computed: {
      hasData() {
        return this.categories.length > 0 && this.values.length > 0;
      },
      totalValue() {
        return this.values.reduce((sum, value) => sum + value, 0);
      },
      percentages() {
        return this.values.map(value => ((value / this.totalValue) * 100).toFixed(1));
      }
    },
    watch: {
      categories() {
        this.updateChart();
      },
      values() {
        this.updateChart();
      },
      chartType() {
        this.recreateChart();
      }
    },
    mounted() {
      this.createChart();
    },
    methods: {
      createChart() {
        if (!this.hasData) return;
        
        const ctx = this.$refs.pieChartCanvas.getContext('2d');
        
        this.chartInstance = new Chart(ctx, {
          type: this.chartType,
          data: {
            labels: this.categories,
            datasets: [{
              data: this.values,
              backgroundColor: this.ensureEnoughColors(),
              hoverOffset: 15
            }],
          },
          options: {
            responsive: true,
            maintainAspectRatio: true,
            parsing: false,
            normalized: true,
            plugins: {
              tooltip: {
                enabled: true,
                callbacks: {
                  label: (context) => {
                    const percentage = this.percentages[context.dataIndex];
                    return `${context.label}: $${context.raw} (${percentage}%)`;
                  }
                }
              },
              legend: {
                position: 'bottom',
                labels: {
                  padding: 20,
                  usePointStyle: true,
                  pointStyle: 'circle'
                }
              }
            },
            events: ['mousemove', 'mouseout', 'click', 'touchstart', 'touchmove'],
            interaction: {
              mode: 'nearest',
              intersect: true
            }
          },
        });
        
        // Set up event handlers and store references to them
        this.setupEventHandlers();
      },
      setupEventHandlers() {
        // Store references to handlers so we can remove them later
        this.clickHandler = this.handleClick.bind(this);
        this.moveHandler = this.handleMouseMove.bind(this);
        
        const canvas = this.$refs.pieChartCanvas;
        
        // Add event listeners
        canvas.addEventListener('click', this.clickHandler);
        canvas.addEventListener('mousemove', this.moveHandler);
      },
      handleClick(evt) {
        if (!this.chartInstance) return;
        
        const chart = this.chartInstance;
        const points = chart.getElementsAtEventForMode(
          evt, 
          'nearest', 
          { intersect: true }, 
          false
        );
        
        if (points.length) {
          const firstPoint = points[0];
          const index = firstPoint.index;
          
          // Emit the event with comprehensive data
          this.$emit('slice-click', {
            index,
            category: this.categories[index],
            value: this.values[index],
            percentage: this.percentages[index],
            color: this.chartInstance.data.datasets[0].backgroundColor[index]
          });
        }
      },
      handleMouseMove(evt) {
        if (!this.chartInstance) return;
        
        const chart = this.chartInstance;
        const points = chart.getElementsAtEventForMode(
          evt, 
          'nearest', 
          { intersect: true }, 
          false
        );
        
        const canvas = this.$refs.pieChartCanvas;
        canvas.style.cursor = points.length ? 'pointer' : 'default';
      },
      updateChart() {
        if (this.chartInstance) {
            try {
            // Update the chart data with the current props values
            this.chartInstance.data.labels = this.categories;
            this.chartInstance.data.datasets[0].data = this.values;
            this.chartInstance.data.datasets[0].backgroundColor = this.ensureEnoughColors();
            
            // Update the chart
            this.chartInstance.update();
            } catch (error) {
            console.error('Error updating chart:', error);
            }
        } else {
            this.createChart();
        }
      },

      recreateChart() {
        if (this.chartInstance) {
          this.chartInstance.destroy();
          this.chartInstance = null;
        }
        this.createChart();
      },
      ensureEnoughColors() {
        if (this.categories.length <= this.colors.length) {
          return this.colors.slice(0, this.categories.length);
        }
        
        // Need more colors than provided
        const colors = [...this.colors];
        for (let i = colors.length; i < this.categories.length; i++) {
          const randomColor = '#' + Math.floor(Math.random()*16777215).toString(16);
          colors.push(randomColor);
        }
        return colors;
      },
      cleanupEventListeners() {
        if (this.$refs.pieChartCanvas) {
          const canvas = this.$refs.pieChartCanvas;
          if (this.clickHandler) canvas.removeEventListener('click', this.clickHandler);
          if (this.moveHandler) canvas.removeEventListener('mousemove', this.moveHandler);
        }
      }
    },
    beforeUnmount() {
      // Proper cleanup for Vue 3
      this.cleanupEventListeners();
      if (this.chartInstance) {
        this.chartInstance.destroy();
      }
    },
    // For Vue 2 compatibility
    beforeDestroy() {
      this.cleanupEventListeners();
      if (this.chartInstance) {
        this.chartInstance.destroy();
      }
    }
  };
  </script>
  
  <style scoped>
  .chart-container {
    position: relative;
    width: 100%;
    max-height: 400px;
    margin: 0 auto;
    border: 0;
    elevation: 0;
  }
  
  /* Responsive breakpoints */
  @media (min-width: 600px) {
    .chart-container {
      max-width: 400px;
    }
  }
  </style>
