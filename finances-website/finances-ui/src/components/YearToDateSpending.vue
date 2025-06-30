<template>
    <v-container fluid>
        <v-row justify="end">
            <v-col cols="3">
                <v-autocomplete
                    label="Select Year to Display"
                    v-model="selectedYear"
                    :items="years"
                >
                </v-autocomplete>
            </v-col>
        </v-row>
        <v-row justify="center">
            <v-col cols="12">
                <v-card rounded="lg" elevation="16">
                    <v-card-title align="center">
                        Spending by Month YTD, Average Net ${{ avgNet[selectedYear] }}
                    </v-card-title>
                    <v-card-text>
                        <bar-chart
                            :data="spendingYearToDateMonth"
                            category-field="month"
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
                        Spending by Category YTD
                    </v-card-title>
                    <v-card-text>
                        <bar-chart
                            :data="spendingYearToDateCat"
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
    </v-container>
</template>

<script>
import ApiRequests from "@/api/requests";
import BarChart from '@/components/BarChart.vue'

export default {
    name: 'YearToDateSpending',
    components: {
        BarChart,
    },
    data() {
        return {
            avgNet: {},
            categories: {},
            catSpendingData: null,
            orderedCategories: [],
            selectedYear: new Date().getFullYear().toString(),
            spendingData: null,
            spendingLoading: false,
            years: []
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

    computed: {
        spendingYearToDateMonth() {
            if (!this.spendingData || 
                !this.spendingData[this.selectedYear]) {
                return  [{'month': '', 'spending': 0, 'budget': 0}];
            }
            return Object.entries(this.spendingData[this.selectedYear]).map(([month, amount]) => ({
                month: month,
                spending: amount[0],
                budget: amount[1]
            }));
        },

        spendingYearToDateCat() {
            if (!this.catSpendingData || 
                !this.catSpendingData[this.selectedYear]) {
                return  [{'category': '', 'spending': 0, 'budget': 0}];
            }
            return Object.entries(this.catSpendingData[this.selectedYear]).map(([category, amount]) => ({
                category: this.toProperCase(category),
                spending: amount[0],
                budget: amount[1]
            }));
        }
    },

    mounted() {
        this.spendingLoading = true;
        this.sortedCategories();
        this.getSpendingYearToDate();
        this.getSpendingYearToDateCategorized();
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
        },

        async sortedCategories() {
            await this.getCategories();
            this.orderedCategories = Array(Object.keys(this.categories).length).fill(null);
            Object.entries(this.categories).forEach(([category, rank]) => {
                let position = rank - 1
                this.orderedCategories[position] = category;
            });
        },

        async getSpendingYearToDate() {
            const response = await ApiRequests.getSpendingYearToDate();
            this.spendingData = response.data.spending;
            this.years = Object.keys(this.spendingData);
            this.avgNet = response.data.avg;
        },

        async getSpendingYearToDateCategorized() {
            const response = await ApiRequests.getSpendingYearToDateCategorized();
            this.catSpendingData = response.data;
            this.spendingLoading = false;
        },

        toProperCase(str) {
            return str.split(' ')
                .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
                .join(' ');
        }
    }
}
</script>