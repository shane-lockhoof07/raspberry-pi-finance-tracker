<template>
    <v-progress-linear
        :active="rentLoading"
        :indeterminate="rentLoading"
        color="#FFFFFF"
    ></v-progress-linear>
    <v-container fluid>
        <v-row>
            <v-col cols="12">
                <v-card elevation="16">
                    <v-card-title>
                        Rent for {{ year }}
                    </v-card-title>
                    <v-card-text>
                        <v-row>
                            <reactive-bar-chart
                                ref="barChart"
                                :key="'rent-chart-' + year + '-' + chartKey"
                                :data="rentData"
                                category-field="month"
                                :value-fields="['value']"
                                :series-names="['Rent']"
                                :colors="['#ff5d5dff']"
                                height="460px"
                                :loading="rentLoading"
                                legend-text-color="#FFFFFF"
                                sort-field="monthIndex"
                                :enable-zoom="false"
                                @bar-click="handleBarClick"
                            >
                                <template v-slot:empty>
                                    <v-alert
                                        type="info"
                                        text="No rent data available for this year"
                                        class="ma-4"
                                    ></v-alert>
                                </template>
                            </reactive-bar-chart>
                        </v-row>
                        <v-row align="center">
                            <v-col cols="12" sm="3" md="3" align="center">
                                <div class="text-subtitle-1">Total Annual Rent</div>
                                <div class="text-h5">{{ formatCurrency(totalRent) }}</div>
                            </v-col>
                            <v-col cols="12" sm="3" md="3" align="center">
                                <div class="text-subtitle-1">Monthly Average</div>
                                <div class="text-h5">{{ formatCurrency(averageRent) }}</div>
                            </v-col>
                            <v-col cols="12" sm="3" md="3" align="center">
                                <div class="text-subtitle-1">Highest Month</div>
                                <div class="text-h5">{{ highestMonth }}</div>
                                <div class="text-subtitle-2">{{ formatCurrency(highestRent) }}</div>
                            </v-col>
                            <v-col cols="12" sm="3" md="3" align="center">
                                <div class="text-subtitle-1">Lowest Month</div>
                                <div class="text-h5">{{ lowestMonth }}</div>
                                <div class="text-subtitle-2">{{ formatCurrency(lowestRent) }}</div>
                            </v-col>
                        </v-row>

                    </v-card-text>
                </v-card>
            </v-col>
        </v-row>

        <!-- Add Rent Form -->
        <v-row class="mt-4">
            <v-col cols="12">
                <v-card elevation="8">
                    <v-card-title>Add New Rent</v-card-title>
                    <v-card-text>
                        <v-form ref="rentForm" @submit.prevent="addRent">
                            <v-row>
                                <v-col cols="12" sm="6" md="4">
                                    <v-text-field
                                        label="Rent Amount"
                                        v-model="newRent"
                                        type="number"
                                        :rules="rentRules"
                                        prefix="$"
                                        density="comfortable"
                                        autofocus
                                        :disabled="rentLoading"
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
                                        :disabled="rentLoading"
                                    >
                                    </v-autocomplete>
                                </v-col>
                                <v-col cols="12" sm="12" md="4">
                                    <v-btn
                                        block
                                        size="x-large" rounded="lg"
                                        color="primary"
                                        type="submit"
                                        :loading="rentLoading"
                                        :disabled="!isFormValid || rentLoading"
                                    >
                                        Add Rent
                                    </v-btn>
                                </v-col>
                            </v-row>
                        </v-form>
                    </v-card-text>
                </v-card>
            </v-col>
        </v-row>
    </v-container>

    <!-- Update Rent Dialog -->
    <v-dialog v-model="updateDialog" max-width="500px">
        <v-card elevation="16">
            <v-card-title>
                Update Rent for {{ selectedMonth }} {{ year }}
            </v-card-title>
            <v-card-text>
                <v-form ref="updateForm" @submit.prevent="updateRent">
                    <v-row>
                        <v-col cols="12">
                            <p><strong>Current Rent:</strong> {{ formatCurrency(selectedValue) }}</p>
                        </v-col>
                    </v-row>
                    <v-row>
                        <v-col cols="12">
                            <v-text-field
                                label="New Rent Amount"
                                v-model="updatedRent"
                                type="number"
                                :rules="rentRules"
                                prefix="$"
                                autofocus
                                :disabled="rentLoading"
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
                    @click="deleteRent" 
                    :disabled="rentLoading"
                >
                    Delete
                </v-btn>
                <v-spacer></v-spacer>
                <v-btn 
                    color="primary" 
                    variant="text" 
                    @click="updateRent"
                    :loading="rentLoading"
                    :disabled="!isUpdateFormValid || rentLoading"
                >
                    Update
                </v-btn>
                <v-btn 
                    variant="text" 
                    @click="updateDialog = false"
                    :disabled="rentLoading"
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

export default {
    props: {
        rent: {
            type: Object,
            default: () => ({})
        },
        year: {
            type: String,
            required: true
        },
        years: {
            type: Array,
            default: () => []
        }
    },
    name: 'Rent',
    components: {
        ReactiveBarChart,
    },
    data() {
        return {
            rentLoading: false,
            updateDialog: false,
            confirmDialog: false,
            confirmMessage: '',
            confirmCallback: null,
            months: [
                'January', 'February', 'March', 'April', 
                'May', 'June', 'July', 'August', 
                'September', 'October', 'November', 'December'
            ],
            newRent: null,
            newMonth: null,
            nextMonth: null,
            rentPage: {},
            selectedMonth: '',
            selectedValue: 0,
            selectedBarData: null,
            updatedRent: null,
            chartKey: 0,
            rentRules: [
                v => !!v || 'Rent amount is required',
                v => v >= 0 || 'Rent cannot be negative',
                v => v <= 50000 || 'Value seems too large (max $50,000)'
            ]
        }
    },

    computed: {
        rentData() {
            if (!this.rentPage || !this.rentPage[this.year]) {
                console.log('No rent data for year', this.year);
                return [];
            }
            
            const yearData = this.rentPage[this.year];
            
            const result = this.months.map((month, index) => {
                const value = yearData[month] !== undefined ? Number(yearData[month]) : 0;
                
                return {
                    month,
                    monthIndex: index,
                    value: value
                };
            });
            
            console.log('Rent data for chart:', result);
            return result;
        },

        hasRentData() {
            return this.rentData.some(item => item.value > 0);
        },

        totalRent() {
            return this.rentData.reduce((sum, item) => sum + item.value, 0);
        },

        averageRent() {
            const nonZeroMonths = this.rentData.filter(item => item.value > 0);
            if (nonZeroMonths.length === 0) return 0;
            return this.totalRent / nonZeroMonths.length;
        },

        highestRent() {
            if (!this.hasRentData) return 0;
            return Math.max(...this.rentData.map(item => item.value));
        },

        highestMonth() {
            if (!this.hasRentData) return 'None';
            const highestItem = this.rentData.find(item => item.value === this.highestRent);
            return highestItem ? highestItem.month : 'None';
        },

        lowestRent() {
            if (!this.hasRentData) return 0;
            const nonZeroRents = this.rentData.filter(item => item.value > 0);
            if (nonZeroRents.length === 0) return 0;
            return Math.min(...nonZeroRents.map(item => item.value));
        },

        lowestMonth() {
            if (!this.hasRentData) return 'None';
            const nonZeroRents = this.rentData.filter(item => item.value > 0);
            if (nonZeroRents.length === 0) return 'None';
            const lowestItem = nonZeroRents.find(item => item.value === this.lowestRent);
            return lowestItem ? lowestItem.month : 'None';
        },

        isFormValid() {
            return parseFloat(this.newRent) >= 0 && this.newMonth;
        },

        isUpdateFormValid() {
            return this.updatedRent !== null && this.updatedRent >= 0;
        }
    },

    watch: {
        year(newValue) {
            this.chartKey += 1;
            this.updateNextAvailableMonth();
        },
        rent: {
            handler(newValue) {
                if (newValue && Object.keys(newValue).length > 0) {
                    this.rentPage = newValue;
                    this.updateNextAvailableMonth();
                }
            },
            immediate: true,
            deep: true
        }
    },

    created() {
        const currentDate = new Date();
        this.newMonth = this.months[currentDate.getMonth()];
    },

    mounted() {
        if (!this.rent || Object.keys(this.rent).length === 0) {
            this.rentLoading = true;
            this.getRent();
        } else {
            this.rentPage = this.rent;
            this.updateNextAvailableMonth();
        }
    },

    methods: {
        updateNextAvailableMonth() {
            this.newMonth = this.months[new Date().getMonth()];
        },

        async getRent() {
            try {
                const response = await ApiRequests.getRent();
                this.rentPage = response.data;
                this.updateNextAvailableMonth();
            } catch (e) {
                console.error("Failed to fetch rent data:", e);
                this.showError("Failed to load rent data. Please try again.");
            } finally {
                this.rentLoading = false;
            }
        },

        async addRent() {
            if (!this.isFormValid) return;
            
            const rentAmount = parseFloat(this.newRent);
            
            const data = {
                'year': this.year,
                'month': this.newMonth,
                'amount': rentAmount
            };
            
            this.rentLoading = true;
            
            try {
                const response = await ApiRequests.addRent(data);
                this.rentPage = response.data;
                
                this.updateNextAvailableMonth();
                this.newRent = null;
                
                this.chartKey += 1;
                if (this.$refs.rentForm) {
                    this.$refs.rentForm.reset();
                }
                
            } catch (e) {
                console.error("Failed to add rent:", e);
                this.showError("Failed to add rent. Please try again.");
            } finally {
                this.rentLoading = false;
            }
        },

        async updateRent() {
            if (!this.isUpdateFormValid) return;

            const rentAmount = parseFloat(this.updatedRent);
            
            const data = {
                'year': this.year,
                'month': this.selectedMonth,
                'amount': rentAmount
            };
            
            this.rentLoading = true;
            
            try {
                const response = await ApiRequests.updateRent(data);
                this.rentPage = response.data;
                
                this.updateNextAvailableMonth();
                this.chartKey += 1;
                this.updateDialog = false;
                
            } catch (e) {
                console.error("Failed to update rent:", e);
                this.showError("Failed to update rent. Please try again.");
            } finally {
                this.rentLoading = false;
            }
        },

        deleteRent() {
            this.confirmMessage = `Are you sure you want to delete rent data for ${this.selectedMonth} ${this.year}?`;
            this.confirmCallback = this.confirmDeleteRent;
            this.confirmDialog = true;
        },

        async confirmDeleteRent() {
            this.rentLoading = true;
            
            try {
                const data = {
                    'year': this.year,
                    'month': this.selectedMonth,
                    'amount': 0 
                };
                
                const response = await ApiRequests.updateRent(data);
                this.rentPage = response.data;
                
                this.updateNextAvailableMonth();
                this.chartKey += 1;
                
                this.updateDialog = false;
                this.confirmDialog = false;
                
            } catch (e) {
                console.error("Failed to delete rent:", e);
                this.showError("Failed to delete rent. Please try again.");
            } finally {
                this.rentLoading = false;
            }
        },

        handleBarClick(data) {
            this.selectedMonth = data.category;
            this.selectedValue = data.value;
            this.selectedBarData = data.fullData;
            this.updatedRent = data.value;
            this.updateDialog = true;
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

@media (max-width: 600px) {
    .v-col {
        padding: 8px;
    }
}
</style>