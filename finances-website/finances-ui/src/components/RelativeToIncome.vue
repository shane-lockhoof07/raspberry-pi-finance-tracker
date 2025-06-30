<template>
    <v-container fluid>
        <v-card elevation="16">
            <v-card-title>
                Monthly Financial Overview {{ selectedYear }}, Net Average {{ formatCurrency(netSavings[selectedYear]) }}
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
                <stacked-bar-chart
                    ref="stackedChart"
                    :key="selectedYear"
                    :data="chartData"
                    category-field="month"
                    :stacked-fields="['investments', 'rent', 'spending', 'moneyTransfers']"
                    :income-fields="['disposableIncome', 'extraIncome']"
                    :stacked-names="['Investments', 'Rent', 'Spending', 'Money Transfers']"
                    :income-names="['Disposable Income', 'Extra Income']"
                    height="500px"
                    :stacked-colors="['#74b9ff', '#55efc4', '#ff7675']"
                    :income-colors="['#a29bfe', '#FFD700']"
                    legend-text-color="#FFFFFF"
                />
            </v-card-text>
        </v-card>        
    </v-container>
</template>

<script>
import ApiRequests from "@/api/requests";
import StackedBarChart from './IncomeStackedBarChart.vue';

export default {
    name: 'FinancialOverview',
    components: {
        StackedBarChart
    },
    data() {
        return {
        selectedYear: '2025',
        netSavings: 0,
        years: ['2025', '2024'],
        detailDialog: false,
        selectedMonth: '',
        selectedCategory: '',
        selectedValue: 0,
        selectedData: null,
        updatedValue: null,
        months: [
            'January', 'February', 'March', 'April', 
            'May', 'June', 'July', 'August', 
            'September', 'October', 'November', 'December'
        ],
        financialData: {}
        }
    },

    computed: {
        chartData() {
            if (!this.financialData || 
                !this.financialData[this.selectedYear]) {
                    return [];
            }
            const yearData = this.financialData[this.selectedYear];
            return Object.values(yearData);
        },
    },

    mounted() {
        if (Object.keys(this.financialData).length < 1) {
            this.getSpendingRelativeToIncome();
        }
    },
    
    watch: {
        years() {
            const currentYear = new Date().getFullYear().toString();
            if (!this.years.includes(currentYear)) {
                this.years.push(currentYear);
            }
        }
    },

    methods: {
        async getSpendingRelativeToIncome() {
            try {
                const response = await ApiRequests.getSpendingRelativeToIncome();
                this.financialData = response.data.data;
                this.netSavings = response.data.avg
                this.years = Object.keys(this.financialData);
            } catch (e) {
                console.log("failed", e);
            }
        },
        
        formatCurrency(value) {
            return new Intl.NumberFormat('en-US', {
                style: 'currency',
                currency: 'USD',
                minimumFractionDigits: 0,
                maximumFractionDigits: 0
            }).format(value);
        }
    }
}
</script>