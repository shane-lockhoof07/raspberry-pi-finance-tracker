<template>
    <v-row>
    <v-col cols="12">
        <v-card elevation="16" class="mb-6">
        <v-card-title>
            Investment Growth Prediction (40 Years)
        </v-card-title>
        <v-card-text>
            <v-row>
            <v-col cols="12" md="4" lg="4">
                <v-text-field
                v-model="monthlyContribution"
                label="Monthly Contribution ($)"
                type="number"
                prefix="$"
                :rules="[val => !!val || 'Required', val => !isNaN(val) || 'Must be a number']"
                @update:model-value="recalculate"
                ></v-text-field>
            </v-col>
            <v-col cols="12" md="4" lg="4">
                <v-text-field
                v-model="currentInvestments"
                label="Current Investment Value ($)"
                type="number"
                prefix="$"
                :rules="[val => !!val || 'Required', val => !isNaN(val) || 'Must be a number']"
                @update:model-value="recalculate "
                ></v-text-field>
            </v-col>
            <v-col cols="12" md="4" lg="4">
                <v-text-field
                v-model="endYear"
                label="End Year"
                type="number"
                @update:model-value="recalculate "
                ></v-text-field>
            </v-col>
            </v-row>
            <v-row>
            <v-col cols="12" lg="8">
                <p v-if="loading">Loading data...</p>
                <base-line-chart
                v-else
                :data="predictionData"
                xField="year"
                :series="chartSeries"
                :colors="chartColors"
                height="500px"
                title="Investment Growth Projection"
                xAxisName="Year"
                yAxisName="Value ($)"
                :formatYAxis="formatCurrencyForAxis"
                />
            </v-col>
            <v-col cols="12" lg="4">
                <v-card variant="outlined" class="pa-4">
                <div class="text-h6 mb-4">Projection Summary</div>
                <template v-if="summaryValues.length > 0">
                    <v-row v-for="(rate, index) in returnRates" :key="index" class="mb-1">
                    <v-col cols="7">
                        <div class="d-flex align-center">
                        <div class="mr-2" :style="`width: 12px; height: 12px; border-radius: 50%; background-color: ${chartColors[index]}`"></div>
                        <span>{{ rate }}% Return</span>
                        </div>
                    </v-col>
                    <v-col cols="5" class="text-right font-weight-bold">
                        ${{ formatCurrency(summaryValues[index]) }}
                    </v-col>
                    </v-row>
                    <v-divider class="my-3"></v-divider>
                    <div class="text-caption mt-2">
                    Based on ${{ formatCurrency(currentInvestments) }} initial investment with ${{ formatCurrency(monthlyContribution) }} monthly contributions.
                    </div>
                </template>
                <div v-else class="text-body-2">
                    Set your parameters to see projected values.
                </div>
                </v-card>
            </v-col>

            </v-row>
        </v-card-text>
        </v-card>
    </v-col>
    </v-row>

    <!-- Stock Value Prediction Card -->
    <v-row>
    <v-col cols="12">
        <v-card elevation="16">
        <v-card-title>
            Combined Investment & Stock Value Projection (7% Annual Growth)
        </v-card-title>
        <v-card-text>
            <v-row>
            <v-col cols="12" md="6" lg="3">
                <v-text-field
                v-model="sharesCount"
                label="Number of Shares"
                type="number"
                :rules="[val => !!val || 'Required', val => !isNaN(val) || 'Must be a number']"
                @update:model-value="recalculate"
                :hint="`Total possible: ${totalPossibleShares}`"
                persistent-hint
                ></v-text-field>
            </v-col>
            <v-col cols="12" md="6" lg="3">
                <v-text-field
                v-model="shareValueAtIPO"
                label="Expected Share Value at IPO ($)"
                type="number"
                prefix="$"
                :rules="[val => !!val || 'Required', val => !isNaN(val) || 'Must be a number']"
                @update:model-value="recalculate"
                ></v-text-field>
            </v-col>
            <v-col cols="12" md="6" lg="3">
                <v-text-field
                v-model="ipoYear"
                label="Expected IPO Year"
                type="number"
                :rules="[val => !!val || 'Required', val => !isNaN(val) || 'Must be a number']"
                @update:model-value="recalculate"
                ></v-text-field>
            </v-col>
            <v-col cols="12" md="6" lg="3">
                <v-row>
                <v-col cols="12">
                    <div class="mt-2 d-flex align-center">
                        <div class="text-h5 font-weight-bold mr-2">Vested Shares: </div>
                        <div class="text-h5 font-weight-bold mr-2">{{ formatNumber(vestedShares) }}</div>
                    </div>
                    <div class="mt-1 text-caption">
                    {{ stockLoadingError ? stockLoadingError : `As of ${new Date().toLocaleDateString()}` }}
                    </div>
                </v-col>
                </v-row>
            </v-col>
            </v-row>

            <v-row class="mt-4">
            <v-col cols="12" lg="8">
                <p v-if="stockLoading">Loading stock data...</p>
                <base-line-chart
                v-else-if="stockPredictionData.length > 0"
                :data="stockPredictionData"
                xField="year"
                :series="stockChartSeries"
                :colors="stockChartColors"
                height="500px"
                title="Combined Investment & Stock Growth (7% Annual Return)"
                xAxisName="Year"
                yAxisName="Value ($)"
                :formatYAxis="formatCurrencyForAxis"
                />
                <p v-else>No stock data available. Please check your inputs.</p>
            </v-col>
            <v-col cols="12" lg="4">
                <v-card variant="outlined" class="pa-4">
                <div class="text-h6 mb-4">Projected Stock Values</div>
                <template v-if="stockSummaryValues.length > 0">
                    <v-row v-for="(value, index) in stockSummaryValues" :key="index" class="mb-2">
                    <v-col cols="4">
                        <div class="d-flex align-center">
                        <div class="mr-2" :style="`width: 12px; height: 12px; border-radius: 50%; background-color: ${stockChartColors[index]}`"></div>
                        <span>{{ stockValueMultipliers[index] * 100 }}% of IPO value</span>
                        </div>
                    </v-col>
                    <v-col cols="4" class="text-right font-weight-bold">
                        ${{ formatCurrency(value) }}
                    </v-col>
                    <v-col cols="4" class="text-right font-weight-bold">
                        + ${{ formatCurrency(value - get7PercentReturnValue()) }}
                    </v-col>
                    </v-row>
                </template>
                <div v-else class="text-body-2">
                    Set your parameters to see projected values.
                </div>
                </v-card>
            </v-col>
            </v-row>
        </v-card-text>
        </v-card>
    </v-col>
    </v-row>
</template>
  
  <script>
  import ApiRequests from '@/api/requests';
  import BaseLineChart from '@/components/BaseLineChart.vue';
  
  export default {
    name: 'NetWorthPrediction',
    components: {
      BaseLineChart
    },
    props: {
      parentNetWorthData: {
        type: Object,
        default: () => ({})
      }
    },
    data() {
      return {
        // Investment prediction data
        netWorthData: {},
        loading: true,
        monthlyContribution: 2291,
        currentInvestments: 0,
        returnRates: [3, 5, 7, 9, 11],
        chartColors: ['#e74c3c', '#f39c12', '#2ecc71', '#3498db', '#9b59b6'],
        predictionData: [],
        summaryValues: [],
        endYear: 2065,
  
        // Stock prediction data
        stockLoading: true,
        stockLoadingError: null,
        vestedShares: 0, 
        totalPossibleShares: 0,
        sharesCount: 0,
        shareValueAtIPO: 20,
        ipoYear: 2035,
        stockValueMultipliers: [0.5, 0.75, 1.0, 1.25, 1.5],
        stockChartColors: ['#e74c3c', '#f39c12', '#2ecc71', '#3498db', '#9b59b6'],
        stockPredictionData: [],
        stockSummaryValues: [],
        stockVestingData: {}
      };
    },
    computed: {
      chartSeries() {
        return this.returnRates.map(rate => ({
          name: `${rate}% Return`,
          field: `rate${rate}`
        }));
      },
      yearsArray() {
        const currentYear = new Date().getFullYear();
        return Array.from({ length: 41 }, (_, i) => currentYear + i);
      },
      stockChartSeries() {
        return this.stockValueMultipliers.map(multiplier => ({
          name: `${multiplier * 100}% of IPO Value`,
          field: `value${multiplier * 100}`
        }));
      },
      investmentYearsArray() {
        const currentYear = new Date().getFullYear();
        const endYear = parseInt(this.endYear);
        return Array.from(
          { length: endYear - currentYear + 1 }, 
          (_, i) => currentYear + i
        );
      },
      stockYearsArray() {
        const currentYear = new Date().getFullYear();
        const endYear = parseInt(this.endYear);
        return Array.from(
          { length: endYear - currentYear + 1 }, 
          (_, i) => currentYear + i
        );
      }
    },
    async created() {
      try {
        await Promise.all([
          this.getNetWorthData(),
          this.getStockVestingData()
        ]);
        
        this.initializeCurrentInvestment();
        this.calculatePredictions();
        
        this.initializeStockData();
        this.calculateStockPredictions();
      } catch (error) {
        console.error("Error initializing data:", error);
      } finally {
        this.loading = false;
        this.stockLoading = false;
      }
    },
    methods: {
      get7PercentReturnValue() {
        const sevenPercentIndex = this.returnRates.findIndex(rate => rate === 7);
        return sevenPercentIndex >= 0 && this.summaryValues.length > sevenPercentIndex 
          ? this.summaryValues[sevenPercentIndex] 
          : 0;
      },
      
      getDifferenceClass(value) {
        const difference = value - this.get7PercentReturnValue();
        if (difference > 0) return 'green--text';
        if (difference < 0) return 'red--text';
        return '';
      },
      
      async getNetWorthData() {
        try {
          const response = await ApiRequests.getNetWorth();
          if (response && response.data) {
            this.netWorthData = response.data;
          }
        } catch (error) {
          console.error("Failed to get net worth data:", error);
        }
      },
      
      initializeCurrentInvestment() {
        if (this.parentNetWorthData && Object.keys(this.parentNetWorthData).length > 0) {
          this.currentInvestments = this.getMostRecentInvestmentValue(this.parentNetWorthData);
          return;
        }
        
        if (this.netWorthData && Object.keys(this.netWorthData).length > 0) {
          this.currentInvestments = this.getMostRecentInvestmentValue(this.netWorthData);
        }
      },
      
      getMostRecentInvestmentValue(data) {
        let latestYear = 0;
        let latestMonth = '';
        let latestInvestmentValue = 0;
        
        Object.keys(data).forEach(year => {
          if (parseInt(year) > latestYear) {
            latestYear = parseInt(year);
          }
        });
        
        if (latestYear === 0) return 0;
        
        const monthsData = data[latestYear.toString()];
        if (!Array.isArray(monthsData) || monthsData.length === 0) return 0;
        
        const months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
        let latestMonthIndex = -1;
        
        monthsData.forEach(monthData => {
          const monthIndex = months.indexOf(monthData.month);
          if (monthIndex > latestMonthIndex) {
            latestMonthIndex = monthIndex;
            latestMonth = monthData.month;
            latestInvestmentValue = monthData.investments || 0;
          }
        });
        
        return latestInvestmentValue;
      },
      
      calculatePredictions() {
        this.predictionData = [];
        this.summaryValues = [];
        
        const currentYear = new Date().getFullYear();
        const targetYear = parseInt(this.endYear);
        const years = targetYear - currentYear;
        const monthly = parseFloat(this.monthlyContribution);
        const startingAmount = parseFloat(this.currentInvestments);
        
        this.returnRates.forEach((rate, rateIndex) => {
          let yearlyValues = [];
          const rateDecimal = rate / 100;
          let currentValue = startingAmount;
          
          for (let i = 0; i <= this.investmentYearsArray.length; i++) {
            if (i === 0) {
              yearlyValues.push(currentValue);
              continue;
            }
            
            const annualContribution = monthly * 12;
            currentValue = currentValue * (1 + rateDecimal) + annualContribution;
            yearlyValues.push(currentValue);
          }
          
          this.summaryValues[rateIndex] = yearlyValues[yearlyValues.length - 1];
        });
        
        this.predictionData = this.investmentYearsArray.map((year, index) => {
          const dataPoint = { year };
          
          this.returnRates.forEach((rate, rateIndex) => {
            const fieldName = `rate${rate}`;
            const startingAmount = parseFloat(this.currentInvestments);
            const monthly = parseFloat(this.monthlyContribution);
            const rateDecimal = rate / 100;
            
            if (index === 0) {
              dataPoint[fieldName] = startingAmount;
            } else {
              const annualContribution = monthly * 12;
              let currentValue = startingAmount;
              
              for (let i = 1; i <= index; i++) {
                currentValue = currentValue * (1 + rateDecimal) + annualContribution;
              }
              
              dataPoint[fieldName] = currentValue;
            }
          });
          
          return dataPoint;
        });
      },
      
      recalculate() {
        this.calculatePredictions();
        this.calculateStockPredictions();
      },
      
      async getStockVestingData() {
        this.stockLoading = true;
        this.stockLoadingError = null;
        try {
          const response = await ApiRequests.getStockVestingSchedule();
          if (response && response.data) {
            this.stockVestingData = response.data;
            this.vestedShares = response.data.total_vested_shares || 0;
            
            this.totalPossibleShares = 0;
            if (response.data.vesting_schedule) {
              Object.values(response.data.vesting_schedule).forEach(shares => {
                this.totalPossibleShares += parseInt(shares) || 0;
              });
            }
          }
        } catch (error) {
          console.error("Failed to get stock vesting data:", error);
          this.stockLoadingError = "Error loading stock data";
        } finally {
          this.stockLoading = false;
        }
      },
  
      initializeStockData() {
        this.sharesCount = this.vestedShares;
      },
      
      calculateStockPredictions() {
        this.stockPredictionData = [];
        this.stockSummaryValues = [];
        
        const currentYear = new Date().getFullYear();
        const targetYear = parseInt(this.endYear);
        const years = targetYear - currentYear;
        const targetIPOYear = parseInt(this.ipoYear);
        const shareValue = parseFloat(this.shareValueAtIPO);
        const shares = parseInt(this.sharesCount);
        const monthly = parseFloat(this.monthlyContribution);
        const startingAmount = parseFloat(this.currentInvestments);
        
        if (isNaN(targetIPOYear) || isNaN(shareValue) || isNaN(shares)) {
          return;
        }
        
        const annualGrowthRate = 0.07; // 7% annual growth
        
        const investmentValues = [];
        let currentInvestmentValue = startingAmount;
        
        for (let i = 0; i <= this.stockYearsArray.length; i++) {
          if (i === 0) {
            investmentValues.push(currentInvestmentValue);
          } else {
            const annualContribution = monthly * 12;
            currentInvestmentValue = currentInvestmentValue * (1 + annualGrowthRate) + annualContribution;
            investmentValues.push(currentInvestmentValue);
          }
        }
        
        this.stockPredictionData = this.stockYearsArray.map((year, yearIndex) => {
          const dataPoint = { year };
          
          const investmentValue = investmentValues[yearIndex];
          
          this.stockValueMultipliers.forEach(multiplier => {
            const fieldName = `value${multiplier * 100}`;
            
            if (year < targetIPOYear) {
              dataPoint[fieldName] = investmentValue;
            } else {
              const yearsSinceIPO = year - targetIPOYear;
              const growthFactor = Math.pow(1 + annualGrowthRate, yearsSinceIPO);
              const valuePerShare = shareValue * multiplier * growthFactor;
              dataPoint[fieldName] = investmentValue + (valuePerShare * shares);
            }
          });
          
          return dataPoint;
        });
        
        const lastYearIndex = this.stockPredictionData.length - 1;
        if (lastYearIndex >= 0) {
          const lastYearData = this.stockPredictionData[lastYearIndex];
          this.stockValueMultipliers.forEach((multiplier, index) => {
            const fieldName = `value${multiplier * 100}`;
            this.stockSummaryValues[index] = lastYearData[fieldName];
          });
        }
      },
            
      formatCurrency(value) {
        return new Intl.NumberFormat('en-US', {
          maximumFractionDigits: 0
        }).format(Math.round(value));
      },
      
      formatNumber(value) {
        return new Intl.NumberFormat('en-US').format(value);
      },
      
      formatCurrencyForAxis(value) {
        const formattedValue = this.formatCurrency(value);
        if (value >= 1000000) {
          if (value >= 1000000000) {
            const billions = (value / 1000000000).toFixed(2);
            return `$${formattedValue} ($${billions}B)`;
          } else {
            const millions = (value / 1000000).toFixed(2);
            return `$${formattedValue} ($${millions}M)`;
          }
        }
        return '$' + formattedValue;
      }
    },
    watch: {
      parentNetWorthData: {
        handler(newVal) {
          if (newVal && Object.keys(newVal).length > 0) {
            this.initializeCurrentInvestment();
            this.calculatePredictions();
          }
        },
        deep: true
      }
    }
  };
  </script>