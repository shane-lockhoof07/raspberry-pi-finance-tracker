<template>
    <div class="chart-container" :style="{ height }">
      <div v-if="loading" class="chart-loading">
        <v-progress-circular indeterminate color="primary"></v-progress-circular>
      </div>
      <div v-else-if="!hasData" class="chart-empty">
        <slot name="empty">
          <v-alert type="info" text="No data available to display"></v-alert>
        </slot>
      </div>
      <v-chart
        v-else
        ref="chart"
        :key="chartKey"
        :option="chartOption"
        autoresize
        @click="handleChartClick"
      />
    </div>
  </template>
  
  <script>
  import { use } from "echarts/core";
  import { BarChart } from "echarts/charts";
  import {
    TitleComponent,
    TooltipComponent,
    GridComponent,
    LegendComponent,
    DataZoomComponent
  } from "echarts/components";
  import { CanvasRenderer } from "echarts/renderers";
  import VChart from "vue-echarts";
  
  // Register necessary ECharts components
  use([
    BarChart,
    TitleComponent,
    TooltipComponent,
    GridComponent,
    LegendComponent,
    DataZoomComponent,
    CanvasRenderer
  ]);
  
  export default {
    name: "ReactiveBarChart",
    components: {
      VChart
    },
    props: {
      // Data can be passed in multiple formats
      data: {
        type: Array,
        required: true
      },
      // Field in data objects that contains the category (x-axis)
      categoryField: {
        type: String,
        default: "month"
      },
      // Fields in data objects that contain the values (can support multiple series)
      valueFields: {
        type: Array,
        default: () => ["value"]
      },
      // Names for each data series
      seriesNames: {
        type: Array,
        default: () => ["Value"]
      },
      // Colors for each data series
      colors: {
        type: Array,
        default: () => ["#5470c6"]
      },
      // Chart dimensions
      height: {
        type: String,
        default: "400px"
      },
      // Chart title
      title: {
        type: String,
        default: ""
      },
      // Chart subtitle
      subtitle: {
        type: String,
        default: ""
      },
      // Currency to use for formatting
      currency: {
        type: String,
        default: "USD"
      },
      // Loading state
      loading: {
        type: Boolean,
        default: false
      },
      // Legend text color
      legendTextColor: {
        type: String,
        default: "#333333"
      },
      // Enable data zooming for large datasets
      enableZoom: {
        type: Boolean,
        default: false
      },
      // Sort data by category (usually month)
      sortByCategory: {
        type: Boolean,
        default: true
      },
      // Sort field if data should be sorted (e.g., 'monthIndex')
      sortField: {
        type: String,
        default: ""
      }
    },
    data() {
      return {
        chartKey: 0, // Used to force chart re-rendering
        errorMessage: "",
        hoveredIndex: -1
      };
    },
    computed: {
      hasData() {
        // Check if there's valid data with non-zero values
        if (!this.data || this.data.length === 0) return false;
        
        // Check if at least one item has a non-zero value for any of the valueFields
        return this.data.some(item => 
          this.valueFields.some(field => 
            item[field] !== undefined && item[field] !== null && Number(item[field]) > 0
          )
        );
      },
      
      processedData() {
        if (!this.hasData) return [];
  
        // Make a deep copy to avoid modifying the original data
        let result = JSON.parse(JSON.stringify(this.data));
        
        // Filter out entries with no value if valueFields is provided
        if (this.valueFields && this.valueFields.length > 0) {
          result = result.filter(item => {
            // Keep the item if at least one valueField has a non-zero value
            return this.valueFields.some(field => 
              item[field] !== undefined && item[field] !== null && item[field] !== 0
            );
          });
        }
        
        // Sort data if required
        if (this.sortByCategory) {
          if (this.sortField && result.length > 0 && result[0][this.sortField] !== undefined) {
            // Sort by a numeric field if provided (e.g., monthIndex)
            result.sort((a, b) => a[this.sortField] - b[this.sortField]);
          } else {
            // Sort alphabetically by category field
            result.sort((a, b) => {
              const categoryA = String(a[this.categoryField] || "");
              const categoryB = String(b[this.categoryField] || "");
              return categoryA.localeCompare(categoryB);
            });
          }
        }
        
        return result;
      },
      
      categories() {
        // If we have a sortField for month indexes, use that to ensure correct order
        if (this.sortField === 'monthIndex' && this.data.length > 0 && 
            this.data[0][this.sortField] !== undefined) {
          // Get all unique categories from data
          const allCategories = [...new Set(this.data.map(item => item[this.categoryField]))];
          
          // Create a mapping from category to its index
          const categoryToIndex = {};
          this.data.forEach(item => {
            categoryToIndex[item[this.categoryField]] = item[this.sortField];
          });
          
          // Sort categories by their monthIndex
          return allCategories.sort((a, b) => categoryToIndex[a] - categoryToIndex[b]);
        }
        
        // Default to all categories from processed data
        return this.data.map(item => item[this.categoryField]);
      },
      
      series() {
        return this.valueFields.map((field, index) => {
          const seriesName = this.seriesNames[index] || field;
          const color = this.colors[index] || this.colors[0] || "#5470c6";
          
          return {
            name: seriesName,
            type: "bar",
            data: this.categories.map(category => {
              // Find the data item for this category
              const item = this.processedData.find(d => d[this.categoryField] === category);
              // Return the value or 0 if not found
              return item ? (item[field] || 0) : 0;
            }),
            itemStyle: {
              color: color
            },
            emphasis: {
              itemStyle: {
                color: this.darkenColor(color)
              }
            }
          };
        });
      },
      
      chartOption() {
        return {
          title: {
            text: this.title,
            subtext: this.subtitle,
            left: "center",
            textStyle: {
              fontWeight: "normal"
            }
          },
          tooltip: {
            trigger: "item",
            axisPointer: {
              type: "shadow"
            },
            formatter: params => {
              // Handle both single item and array of items
              const paramArray = Array.isArray(params) ? params : [params];
              let result = `${paramArray[0].name}<br>`;
              
              paramArray.forEach(param => {
                result += `${param.seriesName}: ${this.formatCurrency(param.value)}<br>`;
              });
              return result;
            }
          },
          legend: {
            data: this.seriesNames,
            bottom: 0,
            textStyle: {
              color: this.legendTextColor
            }
          },
          grid: {
            left: "3%",
            right: "4%",
            bottom: this.seriesNames.length > 1 ? "50px" : "30px",
            top: this.title ? "60px" : "30px",
            containLabel: true
          },
          xAxis: {
            type: "category",
            data: this.categories,
            axisLabel: {
              interval: 0,
              rotate: this.categories.length > 6 ? 45 : 0
            }
          },
          yAxis: {
            type: "value",
            axisLabel: {
              formatter: value => this.formatShortCurrency(value)
            }
          },
          dataZoom: this.enableZoom ? [
            {
              type: "slider",
              show: true,
              start: 0,
              end: 100,
              height: 20
            }
          ] : [],
          series: this.series
        };
      }
    },
    watch: {
      // Force redraw when key props change
      data: {
        handler() {
          this.updateChart();
        },
        deep: true
      }
    },
    methods: {
      updateChart() {
        this.chartKey += 1;
      },
      
      handleChartClick(params) {
        // Only respond to clicks on the data points
        if (params.componentType === "series") {
          const index = params.dataIndex;
          const seriesIndex = params.seriesIndex;
          const itemData = this.processedData[index];
          const value = itemData[this.valueFields[seriesIndex]];
          const category = itemData[this.categoryField];
          
          // Emit the click event with comprehensive data
          this.$emit("bar-click", {
            index,
            dataIndex: index,
            seriesIndex,
            category,
            value,
            seriesName: this.seriesNames[seriesIndex],
            fullData: itemData
          });
        }
      },
      
      formatCurrency(value) {
        return new Intl.NumberFormat("en-US", {
          style: "currency",
          currency: this.currency,
          minimumFractionDigits: 0,
          maximumFractionDigits: 0
        }).format(value);
      },
      
      formatShortCurrency(value) {
        // Format large numbers with K, M, B suffixes
        if (value >= 1000000000) {
          return "$" + (value / 1000000000).toFixed(1) + "B";
        } else if (value >= 1000000) {
          return "$" + (value / 1000000).toFixed(1) + "M";
        } else if (value >= 1000) {
          return "$" + (value / 1000).toFixed(1) + "K";
        }
        return "$" + value;
      },
      
      // Helper function to darken a color for hover effects
      darkenColor(color) {
        // If color is not a hex value, return as is
        if (!color.startsWith("#")) {
          return color;
        }
        
        // Extract RGB components
        let r, g, b, a = 1;
        
        // Handle different hex formats
        if (color.length === 9) {
          // Format #RRGGBBAA
          r = parseInt(color.slice(1, 3), 16);
          g = parseInt(color.slice(3, 5), 16);
          b = parseInt(color.slice(5, 7), 16);
          a = parseInt(color.slice(7, 9), 16) / 255;
        } else if (color.length === 7) {
          // Format #RRGGBB
          r = parseInt(color.slice(1, 3), 16);
          g = parseInt(color.slice(3, 5), 16);
          b = parseInt(color.slice(5, 7), 16);
        } else {
          // Unsupported format
          return color;
        }
        
        // Darken by 20%
        r = Math.max(0, Math.floor(r * 0.8));
        g = Math.max(0, Math.floor(g * 0.8));
        b = Math.max(0, Math.floor(b * 0.8));
        
        // Return as hex
        if (a < 1) {
          // With alpha
          return `#${r.toString(16).padStart(2, "0")}${g.toString(16).padStart(2, "0")}${b.toString(16).padStart(2, "0")}${Math.round(a * 255).toString(16).padStart(2, "0")}`;
        }
        
        // Without alpha
        return `#${r.toString(16).padStart(2, "0")}${g.toString(16).padStart(2, "0")}${b.toString(16).padStart(2, "0")}`;
      }
    }
  };
  </script>
  
  <style scoped>
  .chart-container {
    width: 100%;
    min-height: 300px;
    position: relative;
  }
  
  .chart-loading,
  .chart-empty {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  .chart-container :deep(.echarts) {
    width: 100%;
    height: 100%;
  }
  </style>