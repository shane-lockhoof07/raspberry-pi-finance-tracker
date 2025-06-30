<template>
    <v-tabs v-model="tab" bg-color="#ccccccff" height="56">
        <v-tab value="recent_spending">Recent Spending</v-tab>
        <v-tab value="year_to_date">Year to Date</v-tab>
        <v-tab value="relative_to_income">Relative to Income</v-tab>
    </v-tabs>
    <v-progress-linear
        :active="spendingLoading"
        :indeterminate="spendingLoading"
        color="#FFFFFF"
    ></v-progress-linear>
    <v-container fluid>
        <v-window v-model="tab">
            <v-window-item value="recent_spending">
                <v-container fluid>
                    <v-row justify="center">
                        <v-col cols="12">
                            <v-card rounded="lg" elevation="16">
                                <v-card-title align="center">
                                    Spending This Month, Net ${{ remainder }}
                                </v-card-title>
                                <v-card-text>
                                    <bar-chart
                                        :data="spendingPast30"
                                        category-field="category"
                                        :value-fields="['spending', 'budget']"
                                        :series-names="['Actual', 'Budget']"
                                        :colors="['#ccccccff', '#fd9223ff']"
                                        height="500px"
                                        legend-text-color="#FFFFFF"
                                    />
                                </v-card-text>
                            </v-card>
                        </v-col>
                    </v-row>
                    <v-row justify="center">
                        <v-col cols="12">
                            <v-card rounded="lg" elevation="16">
                                <v-card-title align="center">
                                    Spending Last Month, Net ${{ lastMonthRemainder }}
                                </v-card-title>
                                <v-card-text>
                                    <bar-chart
                                        :data="spendingLastMonth"
                                        category-field="category"
                                        :value-fields="['spending', 'budget']"
                                        :series-names="['Actual', 'Budget']"
                                        :colors="['#ccccccff', '#fd9223ff']"
                                        height="500px"
                                        legend-text-color="#FFFFFF"
                                    />
                                </v-card-text>
                            </v-card>
                        </v-col>
                    </v-row>
                    <v-row>
                        <v-col cols="6" md="6">
                            <v-autocomplete
                                label="Select a Specific Month"
                                v-model="selectedMonth"
                                :items="months"
                                clearable
                            >
                            </v-autocomplete>  
                        </v-col>
                        <v-col cols="6" md="6">
                            <v-autocomplete
                                label="Select a Specific Year"
                                v-model="selectedYear"
                                :items="years"
                                clearable
                            >
                            </v-autocomplete>   
                        </v-col> 
                    </v-row>
                    <v-row v-if="selectedMonth && selectedYear">
                        <v-col cols="12">
                            <v-card rounded="lg" elevation="16">
                                <v-card-title align="center">
                                    Spending for {{ selectedMonth }} {{ selectedYear }}, Net ${{ specificMonthNet }}
                                    <span v-if="specificMonthLoading">
                                        <v-progress-circular indeterminate size="24"></v-progress-circular>
                                    </span>
                                </v-card-title>
                                <v-card-text v-if="specificMonthData && specificMonthData.length > 1">
                                    <bar-chart
                                        :data="specificMonthData"
                                        category-field="category"
                                        :value-fields="['spending', 'budget']"
                                        :series-names="['Actual', 'Budget']"
                                        :colors="['#ccccccff', '#fd9223ff']"
                                        height="500px"
                                        legend-text-color="#FFFFFF"
                                    />
                                </v-card-text>
                                <v-card-text v-else-if="specificMonthLoading">
                                    <p>Loading data...</p>
                                </v-card-text>
                                <v-card-text v-else>
                                    <p>No data available for {{ selectedMonth }}, {{ selectedYear }}</p>
                                </v-card-text>
                            </v-card>
                        </v-col>
                    </v-row>
                </v-container>
            </v-window-item>
            <v-window-item value="year_to_date">
                <year-to-date-spending>
                </year-to-date-spending>
            </v-window-item>
            <v-window-item value="relative_to_income">
                <relative-to-income>
                </relative-to-income>
            </v-window-item>
        </v-window>
    </v-container>
</template>

<script>
import ApiRequests from "@/api/requests";
import BarChart from '@/components/BarChart.vue'
import YearToDateSpending from '@/components/YearToDateSpending.vue'
import RelativeToIncome from '@/components/RelativeToIncome.vue'


export default {
    name: 'SpendingInformation',
    components: {
        BarChart,
        YearToDateSpending,
        RelativeToIncome
    },
    data() {
        return {
            categories: {},
            currentMonth: new Date().getMonth().toString(),
            lastMonthRemainder: 0,
            months: [
                'January', 'February', 'March', 'April', 
                'May', 'June', 'July', 'August', 
                'September', 'October', 'November', 'December'
            ],
            orderedCategories: [],
            remainder: 0,
            selectedMonth: null,
            selectedYear: new Date().getFullYear().toString(),
            specificMonthData: null,
            specificMonthLoading: false,
            specificMonthCache: {},
            specificMonthNet: 0,
            spendingByMonth: [{'month': {'category': '', 'spending': 0, 'budget': 0}}],
            spendingLastMonth: [{'category': '', 'spending': 0, 'budget': 0}],
            spendingLoading: false,
            spendingPast30: [{'category': '', 'spending': 0, 'budget': 0}],
            tab: "recent_spending",
            years: ['2025']
        }
    },

    computed: {
    },

    watch: {
        years() {
            const currentYear = new Date().getFullYear().toString();
            if (!this.years.includes(currentYear)) {
                this.years.push(currentYear);
            }
        },
        selectedMonth() {
            if (this.selectedMonth && this.selectedYear) {
                this.getSpecificMonthData();
            }
        },
        selectedYear() {
            if (this.selectedMonth && this.selectedYear) {
                this.getSpecificMonthData();
            }
        }
    },

    mounted() {
        if (this.orderedCategories.length == 0) {
            this.sortedCategories();
            this.spendingLoading = true;
        }
        if (this.spendingPast30.length == 1) {
            this.getSpendingPast30Categorized();
            this.spendingLoading = true;
        }
        if (this.spendingLastMonth.length == 1) {
            this.getSpendingLastMonthCategorized();
            this.spendingLoading = true;
        }
        if (this.spendingByMonth.length == 1) {
            this.getSpendingByMonth();
            this.spendingLoading = true;
        }
    },

    methods: {
        async getCategories() {
            try {
                const response = await ApiRequests.getCategories();
                this.categories = response.data;
                return response.data;
            } catch (e) {
                console.log("failed", e);
            }
            this.spendingLoading = false;
        },

        async sortedCategories() {
            await this.getCategories();
            this.orderedCategories = Array(Object.keys(this.categories).length).fill(null);
            Object.entries(this.categories).forEach(([category, rank]) => {
                let position = rank - 1
                this.orderedCategories[position] = category;
            });
            this.spendingLoading = false;
        },

        async getSpendingPast30Categorized() {
            const response = await ApiRequests.getSpendingPast30Categorized();
            const spending = response.data.spending;
            this.remainder = response.data.net;
            this.spendingPast30 = Object.entries(spending).map(([category, amount]) => ({
                category: this.toProperCase(category),
                spending: amount[0],
                budget: amount[1]
            }));
            this.spendingLoading = false;
        },

        async getSpendingLastMonthCategorized() {
            const response = await ApiRequests.getSpendingLastMonthCategorized();
            const spending = response.data.spending;
            this.lastMonthRemainder = response.data.net;
            this.spendingLastMonth = Object.entries(spending).map(([category, amount]) => ({
                category: this.toProperCase(category),
                spending: amount[0],
                budget: amount[1]
            }));
            this.spendingLoading = false;
        },

        async getSpendingByMonth() {
            const response = await ApiRequests.getSpendingLastMonthCategorized();
            this.spendingLoading = false;
        },

        toProperCase(str) {
            return str.split(' ')
                .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
                .join(' ');
        },

        async getSpecificMonthData() {
            const cacheKey = `${this.selectedMonth}-${this.selectedYear}`;
            if (this.specificMonthCache[cacheKey]) {
                this.specificMonthData = this.specificMonthCache[cacheKey].data;
                this.specificMonthNet = this.specificMonthCache[cacheKey].net;
                return;
            }
            
            this.specificMonthLoading = true;
            try {
                const monthNumber = this.months.indexOf(this.selectedMonth) + 1;
                
                const response = await ApiRequests.getSpendingForSpecificMonth(monthNumber, this.selectedYear);
                const spending = response.data.spending;
                const net = response.data.net;
                
                if (spending) {
                    this.specificMonthData = Object.entries(spending).map(([category, amount]) => ({
                        category: this.toProperCase(category),
                        spending: amount[0],
                        budget: amount[1]
                    }));
                    
                    this.specificMonthNet = net;
                    
                    this.specificMonthCache[cacheKey] = {
                        data: this.specificMonthData,
                        net: this.specificMonthNet
                    };
                } else {
                    this.specificMonthData = [];
                }
            } catch (error) {
                console.error("Error fetching specific month data:", error);
                this.specificMonthData = [];
            } finally {
                this.specificMonthLoading = false;
            }
        }
    }
}

</script>

<style scoped>
.v-container {
    margin-top: -8px;
}
</style>