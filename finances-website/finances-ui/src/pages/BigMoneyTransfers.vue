<template>
    <v-layout>
        <v-row no-gutters align="center">
            <v-col cols="12" sm="11" md="11">
                <v-tabs v-model="tab" bg-color="#ccccccff" height="56">
                    <v-tab value="income">Income</v-tab>
                    <v-tab value="rent">Rent</v-tab>
                    <v-tab value="moneyTransfers">Money Transfers</v-tab>
                </v-tabs>
            </v-col>
            <v-col cols="12" sm="1" md="1" class="d-flex align-center px-0">
                <v-autocomplete
                    v-model="year"
                    :items="years"
                    density="compact"
                    variant="plain"
                    bg-color="#ccccccff"
                    hide-details
                    :disabled="bigMoneyLoading"
                    class="year-selector ma-0 pa-0"
                >
                </v-autocomplete>
            </v-col>
        </v-row>
    </v-layout>

    <v-progress-linear
        :active="bigMoneyLoading"
        :indeterminate="bigMoneyLoading"
        color="#FFFFFF"
    ></v-progress-linear>
    <v-window v-model="tab">
        <v-window-item value="income">
            <v-container fluid>
                <v-row>
                    <v-col cols="12">
                        <v-card elevation="16">
                            <v-card-title>
                                After Tax Income for {{ year }}
                            </v-card-title>
                            <v-card-text>
                                <v-row>
                                    <reactive-bar-chart
                                        ref="barChart"
                                        :key="'income-chart-' + year + '-' + chartUpdateTrigger"
                                        :data="incomeData"
                                        category-field="month"
                                        :value-fields="['value']"
                                        :series-names="['Income']"
                                        :colors="['#147228ff']"
                                        height="460px"
                                        :loading="bigMoneyLoading"
                                        legend-text-color="#FFFFFF"
                                        sort-field="monthIndex"
                                        :enable-zoom="false"
                                        @bar-click="handleBarClick"
                                    >
                                        <template v-slot:empty>
                                            <v-alert
                                                type="info"
                                                text="No income data available for this year"
                                                class="ma-4"
                                            ></v-alert>
                                        </template>
                                    </reactive-bar-chart>
                                </v-row>
                                <v-row align="center">
                                    <v-col cols="12" sm="3" md="3" align="center">
                                        <div class="text-subtitle-1">Total Annual Income</div>
                                        <div class="text-h5">{{ formatCurrency(totalIncome) }}</div>
                                    </v-col>
                                    <v-col cols="12" sm="3" md="3" align="center">
                                        <div class="text-subtitle-1">Monthly Average</div>
                                        <div class="text-h5">{{ formatCurrency(averageIncome) }}</div>
                                    </v-col>
                                    <v-col cols="12" sm="3" md="3" align="center">
                                        <div class="text-subtitle-1">Highest Month</div>
                                        <div class="text-h5">{{ highestMonth }}</div>
                                        <div class="text-subtitle-2">{{ formatCurrency(highestIncome) }}</div>
                                    </v-col>
                                    <v-col cols="12" sm="3" md="3" align="center">
                                        <div class="text-subtitle-1">Lowest Month</div>
                                        <div class="text-h5">{{ lowestMonth }}</div>
                                        <div class="text-subtitle-2">{{ formatCurrency(lowestIncome) }}</div>
                                    </v-col>
                                </v-row>
                            </v-card-text>
                            <v-card-actions v-if="debugMode">
                                <v-spacer></v-spacer>
                                <v-btn 
                                    @click="testBarClick" 
                                    color="secondary" 
                                    class="mb-2"
                                >
                                    Test Bar Click
                                </v-btn>
                            </v-card-actions>
                        </v-card>
                    </v-col>
                </v-row>

                <!-- Add Income Form -->
                <v-row class="mt-4">
                    <v-col cols="12">
                        <v-card elevation="8">
                            <v-card-title>Add New Income</v-card-title>
                            <v-card-text>
                                <v-form ref="incomeForm" @submit.prevent="addIncome">
                                    <v-row>
                                        <v-col cols="12" sm="6" md="4">
                                            <v-text-field
                                                label="Income Amount"
                                                v-model="newIncome"
                                                type="number"
                                                :rules="incomeRules"
                                                prefix="$"
                                                density="comfortable"
                                                autofocus
                                                :disabled="bigMoneyLoading"
                                            >
                                            </v-text-field>
                                        </v-col>
                                        <v-col cols="12" sm="6" md="4">
                                            <v-autocomplete
                                                label="Month"
                                                v-model="newMonth"
                                                :items="months"
                                                :rules="[v => !!v || 'Month is required']"
                                                density="comfortable"
                                                :disabled="bigMoneyLoading"
                                            >
                                            </v-autocomplete>
                                        </v-col>
                                        <v-col cols="12" sm="12" md="4">
                                            <v-btn
                                                block
                                                size="x-large" rounded="lg"
                                                color="primary"
                                                type="submit"
                                                :loading="bigMoneyLoading"
                                                :disabled="!isFormValid || bigMoneyLoading"
                                            >
                                                Add Income
                                            </v-btn>
                                        </v-col>
                                    </v-row>
                                </v-form>
                            </v-card-text>
                        </v-card>
                    </v-col>
                </v-row>
            </v-container>
        </v-window-item>
        <v-window-item value="rent">
            <rent
                :rent="rent"
                :year="year"
                :years="years"
            ></rent>
        </v-window-item>
        <v-window-item value="moneyTransfers">
            <money-transfers
                :year="year"
                :years="years"
            ></money-transfers>
        </v-window-item>
    </v-window>

    <!-- Update Income Dialog -->
    <v-dialog v-model="updateDialog" max-width="500px">
        <v-card elevation="16">
            <v-card-title>
                Update Income for {{ selectedMonth }} {{ year }}
            </v-card-title>
            <v-card-text>
                <v-form ref="updateForm" @submit.prevent="updateIncome">
                    <v-row>
                        <v-col cols="12">
                            <p><strong>Current Income:</strong> {{ formatCurrency(selectedValue) }}</p>
                        </v-col>
                    </v-row>
                    <v-row>
                        <v-col cols="12">
                            <v-text-field
                                label="New Income Amount"
                                v-model="updatedIncome"
                                type="number"
                                :rules="incomeRules"
                                prefix="$"
                                autofocus
                                :disabled="bigMoneyLoading"
                            >
                            </v-text-field>
                        </v-col>
                    </v-row>
                </v-form>
            </v-card-text>
            <v-card-actions>
                <v-spacer></v-spacer>
                <v-btn 
                    color="error" 
                    variant="text"
                    @click="deleteIncome" 
                    :disabled="bigMoneyLoading"
                >
                    Delete
                </v-btn>
                <v-spacer></v-spacer>
                <v-btn 
                    color="primary" 
                    variant="text" 
                    @click="updateIncome"
                    :loading="bigMoneyLoading"
                    :disabled="!isUpdateFormValid || bigMoneyLoading"
                >
                    Update
                </v-btn>
                <v-btn 
                    variant="text" 
                    @click="updateDialog = false"
                    :disabled="bigMoneyLoading"
                >
                    Cancel
                </v-btn>
            </v-card-actions>
        </v-card>
    </v-dialog>

    <!-- Confirmation Dialog -->
    <v-dialog v-model="confirmDialog" max-width="400px">
        <v-card>
            <v-card-title>Confirm Action</v-card-title>
            <v-card-text>
                {{ confirmMessage }}
            </v-card-text>
            <v-card-actions>
                <v-spacer></v-spacer>
                <v-btn variant="text" @click="confirmDialog = false">Cancel</v-btn>
                <v-btn 
                    color="error" 
                    variant="text" 
                    @click="confirmAction"
                >
                    Confirm
                </v-btn>
            </v-card-actions>
        </v-card>
    </v-dialog>
</template>

<script>
import ApiRequests from "@/api/requests";
import ReactiveBarChart from '@/components/ReactiveBarChart.vue'
import Rent from "@/components/Rent.vue"
import MoneyTransfers from "@/components/MoneyTransfers.vue"

export default {
    name: 'BigMoneyTransfers',
    components: {
        ReactiveBarChart,
        Rent,
        MoneyTransfers
    },
    data() {
        return {
            bigMoneyLoading: false,
            updateDialog: false,
            confirmDialog: false,
            confirmMessage: '',
            confirmCallback: null,
            income: {}, 
            months: [
                'January', 'February', 'March', 'April', 
                'May', 'June', 'July', 'August', 
                'September', 'October', 'November', 'December'
            ],
            newIncome: null,
            newMonth: null,
            nextMonth: null,
            rent: {}, 
            selectedMonth: '',
            selectedValue: 0,
            selectedBarData: null,
            tab: "income",
            updatedIncome: null,
            year: new Date().getFullYear().toString(),
            years: [],
            chartUpdateTrigger: 0,
            debugMode: false,
            incomeRules: [
                v => !!v || 'Income amount is required',
                v => v >= 0 || 'Income cannot be negative',
                v => v <= 1000000 || 'Value seems too large (max $1,000,000)'
            ]
        }
    },

    computed: {
        incomeData() {
            if (!this.income || !this.income[this.year]) {
                console.log('No income data for year', this.year);
                return [];
            }
            
            const yearData = this.income[this.year];
            
            const result = this.months.map((month, index) => {
                const value = yearData[month] !== undefined ? Number(yearData[month]) : 0;
                
                return {
                    month,
                    monthIndex: index,
                    value: value
                };
            });
            
            return result;
        },

        hasIncomeData() {
            return this.incomeData.some(item => item.value > 0);
        },

        totalIncome() {
            return this.incomeData.reduce((sum, item) => sum + item.value, 0);
        },

        averageIncome() {
            const nonZeroMonths = this.incomeData.filter(item => item.value > 0);
            if (nonZeroMonths.length === 0) return 0;
            return this.totalIncome / nonZeroMonths.length;
        },

        highestIncome() {
            if (!this.hasIncomeData) return 0;
            return Math.max(...this.incomeData.map(item => item.value));
        },

        highestMonth() {
            if (!this.hasIncomeData) return 'None';
            const highestItem = this.incomeData.find(item => item.value === this.highestIncome);
            return highestItem ? highestItem.month : 'None';
        },

        lowestIncome() {
            if (!this.hasIncomeData) return 0;
            const nonZeroIncomes = this.incomeData.filter(item => item.value > 0);
            if (nonZeroIncomes.length === 0) return 0;
            return Math.min(...nonZeroIncomes.map(item => item.value));
        },

        lowestMonth() {
            if (!this.hasIncomeData) return 'None';
            const nonZeroIncomes = this.incomeData.filter(item => item.value > 0);
            if (nonZeroIncomes.length === 0) return 'None';
            const lowestItem = nonZeroIncomes.find(item => item.value === this.lowestIncome);
            return lowestItem ? lowestItem.month : 'None';
        },

        isFormValid() {
            return this.newIncome > 0 && this.newMonth;
        },

        isUpdateFormValid() {
            return this.updatedIncome !== null && this.updatedIncome >= 0;
        }
    },

    watch: {
        year(newValue) {
            this.chartUpdateTrigger += 1;
            this.updateNextAvailableMonth();
        },

        years() {
            const currentYear = new Date().getFullYear().toString();
            if (!this.years.includes(currentYear)) {
                this.years.push(currentYear);
            }
        }
    },

    created() {
        const currentDate = new Date();
        this.newMonth = this.months[currentDate.getMonth()];
        this.year = currentDate.getFullYear().toString();
    },

    mounted() {
        if (!this.income || Object.keys(this.income).length === 0) {
            this.bigMoneyLoading = true;
            this.getIncome();
        }
        
        if (!this.rent || Object.keys(this.rent).length === 0) {
            this.bigMoneyLoading = true;
            this.getRent();
        }
    },

    methods: {
        async getIncome() {
            try {
                const response = await ApiRequests.getIncome();
                this.income = response.data;
                this.years = Object.keys(this.income).sort();                
                
                this.updateNextAvailableMonth();
                this.chartUpdateTrigger += 1;
            } catch (e) {
                console.error("Failed to fetch income data:", e);
                this.showError("Failed to load income data. Please try again.");
            } finally {
                this.bigMoneyLoading = false;
            }
        },

        async getRent() {
            try {
                const response = await ApiRequests.getRent();
                this.rent = response.data;
                
                const rentYears = Object.keys(response.data);
                rentYears.forEach(year => {
                    if (!this.years.includes(year)) {
                        this.years.push(year);
                    }
                });
                this.years.sort();
                
            } catch (e) {
                console.error("Failed to fetch rent data:", e);
                this.showError("Failed to load rent data. Please try again.");
            } finally {
                this.bigMoneyLoading = false;
            }
        },

        updateNextAvailableMonth() {
            this.newMonth = this.months[new Date().getMonth()];
        },

        async addIncome() {
            if (!this.isFormValid) return;
            
            const data = {
                'year': this.year,
                'month': this.newMonth,
                'amount': this.newIncome
            };
            
            this.bigMoneyLoading = true;
            
            try {
                const response = await ApiRequests.addIncome(data);
                this.newIncome = null;
                this.income = response.data;
                this.years = Object.keys(this.income).sort();
                
                this.updateNextAvailableMonth();
                
                this.chartUpdateTrigger += 1;
                this.$refs.incomeForm.reset();
                
            } catch (e) {
                console.error("Failed to add income:", e);
                this.showError("Failed to add income. Please try again.");
            } finally {
                this.bigMoneyLoading = false;
            }
        },

        async updateIncome() {
            if (!this.isUpdateFormValid) return;
            
            const data = {
                'year': this.year,
                'month': this.selectedMonth,
                'amount': this.updatedIncome
            };
            
            this.bigMoneyLoading = true;
            
            try {
                const response = await ApiRequests.updateIncome(data);
                this.income = response.data;
                this.years = Object.keys(this.income).sort();
                
                this.updateNextAvailableMonth();
                
                this.chartUpdateTrigger += 1;
                this.updateDialog = false;
                
            } catch (e) {
                console.error("Failed to update income:", e);
                this.showError("Failed to update income. Please try again.");
            } finally {
                this.bigMoneyLoading = false;
            }
        },

        deleteIncome() {
            this.confirmMessage = `Are you sure you want to delete income data for ${this.selectedMonth} ${this.year}?`;
            this.confirmCallback = this.confirmDeleteIncome;
            this.confirmDialog = true;
        },

        async confirmDeleteIncome() {
            this.bigMoneyLoading = true;
            
            try {
                const data = {
                    'year': this.year,
                    'month': this.selectedMonth,
                    'amount': 0
                };
                
                const response = await ApiRequests.updateIncome(data);
                this.income = response.data;
                this.years = Object.keys(this.income).sort();
                
                this.updateNextAvailableMonth();
                this.chartUpdateTrigger += 1;
                
                this.updateDialog = false;
                this.confirmDialog = false;
                
            } catch (e) {
                console.error("Failed to delete income:", e);
                this.showError("Failed to delete income. Please try again.");
            } finally {
                this.bigMoneyLoading = false;
            }
        },

        handleBarClick(data) {
            this.selectedMonth = data.category;
            this.selectedValue = data.value;
            this.selectedBarData = data.fullData;
            this.updatedIncome = data.value;
            this.updateDialog = true;
        },
        
        testBarClick() {
            if (this.incomeData && this.incomeData.length > 0) {
                const testData = this.incomeData.find(item => item.value > 0) || this.incomeData[0];
                
                this.handleBarClick({
                    category: testData.month,
                    value: testData.value,
                    seriesName: 'Income',
                    fullData: testData
                });
            } else {
                this.showError('No income data available for testing clicks');
            }
        },
        
        formatCurrency(value) {
            return new Intl.NumberFormat('en-US', {
                style: 'currency',
                currency: 'USD',
                minimumFractionDigits: 0,
                maximumFractionDigits: 0
            }).format(value);
        },

        showError(message) {
            console.error(message);
        },

        confirmAction() {
            if (typeof this.confirmCallback === 'function') {
                this.confirmCallback();
            }
            this.confirmDialog = false;
        }
    }
}
</script>

<style scoped>
.v-card {
    margin-bottom: 0px;
    margin-top: -5px;
}

.v-card__title {
    font-weight: 500;
    border-bottom: 1px solid rgba(0, 0, 0, 0.12);
    padding-bottom: 12px;
}

.year-selector {
    min-width: 120px;
    height: 56px;
    border-radius: 5;
}

.year-selector :deep(.v-field__input) {
    padding-top: 14px !important;
}

.year-selector :deep(.v-field__field) {
    height: 56px;
}

.year-selector :deep(.v-field) {
    border-radius: 0;
    box-shadow: none;
    background-color: #ccccccff;
}

.year-selector :deep(.v-field__append-inner) {
    padding-top: 20px;
}

/* Make the tabs and year selector responsive */
@media (max-width: 600px) {
    .v-col {
        padding: 8px;
    }
    
    /* On small screens, ensure year selector is centered */
    .year-selector {
        width: 100%;
        max-width: 200px;
        margin: 0 auto;
    }
}
</style>