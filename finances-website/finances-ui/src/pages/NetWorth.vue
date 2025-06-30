<template>
    <v-row no-gutters align="center">
        <v-col cols="12" sm="12" md="12">
            <v-tabs v-model="tab" bg-color="#ccccccff" height="56">
                <v-tab value="net_worth">Net Worth</v-tab>
                <v-tab value="net_worth_prediction">Net Worth Prediction</v-tab>
                <v-tab value="retirement_calculator">Retirement Calculator</v-tab>
                <v-tab value="stock_vesting">Stock Vesting Schedule</v-tab>
            </v-tabs>
        </v-col>
    </v-row>
    <v-container fluid>
        <v-window v-model="tab" class="pa-0">
            <v-window-item value="net_worth">
                <v-row>
                    <v-col cols="12">
                        <v-card elevation="16">
                            <v-card-title>
                                Net Worth for {{ selectedYear }}
                            </v-card-title>
                            <v-card-text>
                                <v-row>
                                    <v-col cols="3">
                                        <v-select
                                        label="Select Year"
                                        v-model="selectedYear"
                                        :items="years"
                                        ></v-select>
                                    </v-col>
                                </v-row>
                                <p v-if="netWorthLoading">Loading data...</p>
                                <p v-else-if="!hasData">No data available for {{ selectedYear }}</p>
                                <stacked-bar-chart
                                    v-else
                                    ref="stackedChart"
                                    :key="chartKey"
                                    :data="netWorth"
                                    category-field="month"
                                    :stackedFields="['savings', 'investments']"
                                    :stackedNames="['Savings', 'Investments']"
                                    height="500px"
                                    :stackedColors="['#74b9ff', '#55efc4']"
                                    legend-text-color="#FFFFFF"
                                />
                            </v-card-text>
                        </v-card> 
                    </v-col>
                </v-row>
                <v-row>
                    <v-col cols="3" md="3">
                        <v-text-field
                            label="Amount"
                            v-model="amount"
                        />
                    </v-col>
                    <v-col cols="2" md="2">
                        <v-autocomplete
                            label="Type"
                            v-model="type"
                            :items="types"
                        >
                        </v-autocomplete>
                    </v-col>
                    <v-col cols="2" md="2">
                        <v-autocomplete
                            label="Month"
                            v-model="month"
                            :items="months"
                        >
                        </v-autocomplete>
                    </v-col>
                    <v-col cols="2" md="2">
                        <v-autocomplete
                            label="Year"
                            v-model="year"
                            :items="years"
                        >
                        </v-autocomplete>
                    </v-col>
                    <v-col cols="3" md="3">
                        <v-btn
                            block
                            size="x-large" rounded="lg"
                            color="primary"
                            @click="addNetWorth()"
                        >Add to Net Worth
                        </v-btn>
                    </v-col>
                </v-row>   
            </v-window-item>
            <v-window-item value="net_worth_prediction">
                <net-worth-prediction
                    :parent-net-worth-data="netWorthData"
                >
                </net-worth-prediction>
            </v-window-item>
            <v-window-item value="retirement_calculator">
                <retirement-calculator
                    :parent-net-worth-data="netWorthData"
                >
                </retirement-calculator>
            </v-window-item>
            <v-window-item value="stock_vesting">
                <stock-vesting>
                </stock-vesting>
            </v-window-item>
        </v-window> 
    </v-container>  
</template>

<script>
import ApiRequests from "@/api/requests";
import StackedBarChart from '@/components/BaseStackedBarChart.vue';
import NetWorthPrediction from "@/components/NetWorthPrediction.vue";
import StockVesting from "@/components/StockVesting.vue";
import RetirementCalculator from "@/components/RetirementCalculator.vue";

export default {
    name: 'NetWorth',
    components: {
        StackedBarChart,
        NetWorthPrediction,
        StockVesting,
        RetirementCalculator
    },
    data() {
        return {
            amount: null,
            netWorthData: {},
            netWorthLoading: true,
            month: null,
            months: [
                'January', 'February', 'March', 'April', 
                'May', 'June', 'July', 'August', 
                'September', 'October', 'November', 'December'
            ],
            selectedYear: new Date().getFullYear().toString(),
            tab: 'net_worth',
            type: null,
            types: ['Savings', 'Investments'],
            year: new Date().getFullYear().toString(),
            years: ['2025', '2026'],
            chartKey: 0
        }
    },

    computed: {
        netWorth() {
            if (!this.netWorthData || !this.netWorthData[this.selectedYear]) {
                return [];
            }
            
            const yearData = this.netWorthData[this.selectedYear];
            if (!Array.isArray(yearData)) {
                console.error('Net worth data is not an array:', yearData);
                return [];
            }
            
            return yearData.map(item => {
                if (!item || typeof item !== 'object') {
                    return { month: '', savings: 0, investments: 0 };
                }
                
                return {
                    month: item.month || '',
                    savings: Number(item.savings || 0),
                    investments: Number(item.investments || 0)
                };
            });
        },
        
        hasData() {
            return Array.isArray(this.netWorth) && this.netWorth.length > 0;
        }
    },

    async mounted() {
        this.month = this.months[new Date().getMonth()]
        try {
            await this.getNetWorth();
        } catch (error) {
            console.error("Error in mounted:", error);
        } finally {
            this.netWorthLoading = false;
        }
    },

    methods: {
        async getNetWorth() {
            this.netWorthLoading = true;
            try {
                const response = await ApiRequests.getNetWorth();
                if (!response || !response.data) {
                    console.error("Invalid net worth data response:", response);
                    this.netWorthData = {};
                    return {};
                }
                this.netWorthData = response.data;                
                return this.netWorthData;
            } catch (e) {
                console.error("Failed to get net worth data:", e);
                this.netWorthData = {};
                return {};
            } finally {
                this.netWorthLoading = false;
            }
        },

        async addNetWorth() {
            this.netWorthLoading = true;

            const typeKey = this.type.toLowerCase();

            var data = {
                "year": this.year,
                "month": this.month,
                "type": typeKey,
                "amount": this.amount
            }
            try {
                const response = await ApiRequests.addNetWorth(data);
                if (!response || !response.data) {
                    console.error("Invalid net worth data response:", response);
                    this.netWorthData = {};
                    return {};
                }
                this.netWorthData = response.data; 
                this.chartKey++;
                this.amount = null;         
                     
                return this.netWorthData;
            } catch (e) {
                console.error("Failed to get net worth data:", e);
                this.netWorthData = {};
                return {};
            } finally {
                this.netWorthLoading = false;
            }
        }
    },
    
    watch: {
        selectedYear() {
            this.chartKey++;
            
            this.$nextTick(() => {
                if (this.$refs.stackedChart && this.$refs.stackedChart.$refs.chart) {
                    this.$refs.stackedChart.$refs.chart.resize();
                }
            });
        },
        
        years() {
            const currentYear = new Date().getFullYear().toString();
            if (!this.years.includes(currentYear)) {
                this.years.push(currentYear);
            }
        }
    }
}
</script>

<style scoped>
.v-container {
    margin-top: 0px;
}
</style>