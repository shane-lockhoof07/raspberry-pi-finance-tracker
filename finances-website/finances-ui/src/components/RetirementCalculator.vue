<template>
    <v-row align="center" justify="center">
        <v-col cols="12" md="12">
            <div>
                <h2>Needed in Retirment (Current Dollars): {{ formatCurrencyForAxis(minCurrent) }} - {{ formatCurrencyForAxis(maxCurrent) }}, Needed in Retirement (2060 Dollars): {{ formatCurrencyForAxis(minFuture) }} - {{ formatCurrencyForAxis(maxFuture) }}</h2>
            </div>
        </v-col>
    </v-row>
    <v-row class="fill-height">
        <v-col cols="12" md="3" class="d-flex flex-column">
            <v-data-table
                :headers="assumptionsHeaders"
                :items="assumptions"
                hide-default-footer
                items-per-page="-1"
            >
                <template v-slot:item.value="{ item }">
                    <v-text-field
                        v-model="item.value"
                        variant="outlined"
                        density="compact"
                        type="number"
                        hide-details
                        @input="recalculate"
                        :prefix="shouldShowPrefix(item.assumption) ? '$' : ''"
                    ></v-text-field>
                </template>
            </v-data-table>
        </v-col>
        <v-col cols="12" md="9" class="no-padding">
            <v-row class="flex-grow-1">
                <v-col cols="12" md="12">
                    <v-data-table
                        :headers="retirementNeeds.headers"
                        :items="retirementNeeds.data"
                        hide-default-footer
                        items-per-page="-1"
                    >
                        <template v-slot:item.current_value="{ item }">
                          <p>{{ formatCurrencyForAxis(item.current_value) }}</p>
                        </template>
                        <template v-slot:item.future_value="{ item }">
                          <p>{{ formatCurrencyForAxis(item.future_value) }}</p>
                        </template>
                        <template v-slot:item.nest_egg="{ item }">
                          <p>{{ formatCurrencyForAxis(item.nest_egg) }}</p>
                        </template>
                        <template v-slot:item.pmt="{ item }">
                          <p :class="{ 'border': item.pmt < monthlyContribution }">{{ formatCurrencyForAxis(item.pmt) }}</p>
                        </template>
                    </v-data-table>
                </v-col>
            </v-row>
            <v-row class="flex-grow-1">
                <v-col cols="12" md="12">
                    <v-data-table
                        :headers="coastNeeds.headers"
                        :items="coastNeeds.data"
                        hide-default-footer
                        items-per-page="-1"
                    >
                        <template 
                            v-for="key in Object.keys(coastNeeds.data[0] || {})" 
                            :key="key"
                            v-slot:[`item.${key}`]="{ item }"
                        >
                            <template v-if="key !== 'row'">
                                <p v-if="item[key].pmt > monthlyContribution" class="no-border">
                                    {{ item[key].text }}
                                </p>
                                <p v-else class="border">
                                    {{ item[key].text }}
                                </p>
                            </template>
                            <template v-else>
                                {{ item[key] }}
                            </template>
                        </template>
                    </v-data-table>                
                </v-col>
            </v-row>
        </v-col>
    </v-row>
</template>

<script>
import ApiRequests from '@/api/requests';
import BaseLineChart from '@/components/BaseLineChart.vue';

export default {
  name: 'RetirementCalculator',
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
            assumptionsHeaders: [
                { title: 'Assumption', key: 'assumption', align: 'center' },
                { title: 'Value', key: 'value', align: 'center' }
            ],
            assumptions: [
                { assumption: 'Current Investments', value: 120000 },
                { assumption: 'Monthly Contribution', value: 2291 },
                { assumption: 'Rate of Return (%)', value: 8 },
                { assumption: 'Inflation Rate (%)', value: 2.5 },
                { assumption: 'Withdrawal Rate (%)', value: 4 },
                { assumption: 'Mortgage', value: 600000 },
                { assumption: 'Food (Monthly)', value: 1200 },
                { assumption: 'Travel (International)', value: 15000 },
                { assumption: 'Travel (Domestic)', value: 10000 },
                { assumption: 'Hobbies', value: 20000 },
                { assumption: 'Other Spending', value: 20000 },
                { assumption: 'Buffer (%)', value: 20 },
            ],
            coastNeeds: {"headers": [], "data": []},
            maxCurrent: null,
            maxFuture: null,
            minCurrent: null,
            minFuture: null,
            retirementNeeds: [],
        };
    },
  
  computed: {
  },

  async mounted() {
    this.initializeCurrentInvestment();
    this.recalculate();
  },

  methods: {
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
        this.assumptions.find(item => item.assumption === 'Current Investments').value = this.currentInvestments;
        return;
      }
      
      if (this.netWorthData && Object.keys(this.netWorthData).length > 0) {
        this.currentInvestments = this.getMostRecentInvestmentValue(this.netWorthData);
        this.assumptions.find(item => item.assumption === 'Current Investments').value = this.currentInvestments;
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

    async forecastRetirement() {
        const response = await ApiRequests.forecastRetirementNeeds(this.assumptions);
        this.retirementNeeds = response.data;
        const currentValues = this.retirementNeeds.data.map(item => item.current_value);
        const futureValues = this.retirementNeeds.data.map(item => item.future_value);
        this.minCurrent = Math.min(...currentValues);
        this.maxCurrent = Math.max(...currentValues);
        this.minFuture = Math.min(...futureValues);
        this.maxFuture = Math.max(...futureValues);
    },

    async forecastCoast() {
        const response = await ApiRequests.forecastCoastNeeds(this.assumptions);
        this.coastNeeds = response.data;
    },
    
    recalculate() {
      this.forecastRetirement();
      this.forecastCoast();
      this.monthlyContribution = this.assumptions.find(item => item.assumption === 'Monthly Contribution')?.value;
    },
    
    formatCurrency(value) {
      return new Intl.NumberFormat('en-US', {
        maximumFractionDigits: 0
      }).format(Math.round(value));
    },
        
    formatCurrencyForAxis(value) {
      const formattedValue = this.formatCurrency(value);
      return '$' + formattedValue;
    },

    shouldShowPrefix(assumption) {
        const monetaryFields = [
          'Monthly Contribution',
          'Current Investments',
          'Mortgage',
          'Food (Monthly)',
          'Travel (International)',
          'Travel (Domestic)',
          'Hobbies',
          'Other Spending'
        ];
        return monetaryFields.includes(assumption);
    }
  },

  watch: {
    parentNetWorthData: {
      handler(newVal) {
        if (newVal && Object.keys(newVal).length > 0) {
          this.initializeCurrentInvestment();
          this.recalculate();
        }
      },
      deep: true
    }
  }
};
</script>

<style scoped>
.no-padding :deep {
  padding-top: 0px;
}

.v-row.flex-grow-1 {
    margin-bottom: 0px;
    margin-top: 0px;
}

.no-border :deep(.v-field fieldset) {
  border: 0 !important;
  padding: 4px 12px !important;
  text-align: center !important;
}

.border {
  border: 3px solid #4CAF50 !important;
  border-radius: 8px !important;
  padding: 4px 4px !important;
  text-align: center !important;
  background-color: rgba(76, 175, 80, 0.05) !important;
}
</style>
