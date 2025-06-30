<template>
    <v-container fluid>
        <v-progress-linear
            :active="loading"
            :indeterminate="loading"
            color="#FFFFFF"
        ></v-progress-linear>
        
        <!-- Add Money Transfer Form -->
        <v-card elevation="8" class="mb-4">
            <v-card-title>Add New Money Transfer</v-card-title>
            <v-card-text>
                <v-form ref="transferForm" @submit.prevent="addMoneyTransfer">
                    <v-row>
                        <v-col cols="12" sm="6" md="3">
                            <v-text-field
                                label="Amount"
                                v-model="transfer"
                                type="number"
                                prefix="$"
                                :rules="[v => !!v || 'Amount is required']"
                                density="comfortable"
                                :disabled="loading"
                            >
                            </v-text-field>
                        </v-col>
                        <v-col cols="12" sm="6" md="3">
                            <v-autocomplete
                                label="Month"
                                v-model="month"
                                :items="months"
                                :rules="[v => !!v || 'Month is required']"
                                density="comfortable"
                                :disabled="loading"
                            >
                            </v-autocomplete>
                        </v-col>
                        <v-col cols="12" sm="6" md="3">
                            <v-autocomplete
                                label="Type"
                                v-model="type"
                                :items="types"
                                :rules="[v => !!v || 'Type is required']"
                                density="comfortable"
                                :disabled="loading"
                            >
                            </v-autocomplete>
                        </v-col>
                        <v-col cols="12" sm="6" md="3">
                            <v-btn
                                block
                                size="x-large" rounded="lg"
                                color="primary"
                                type="submit"
                                :loading="loading"
                                :disabled="!isFormValid || loading"
                            >Add Transfer
                            </v-btn>
                        </v-col>
                    </v-row>
                    <v-row>
                        <v-col cols="12">
                            <v-text-field
                                label="Description"
                                v-model="description"
                                :rules="[v => !!v || 'Description is required']"
                                density="comfortable"
                                :disabled="loading"
                            >
                            </v-text-field>
                        </v-col>
                    </v-row>
                </v-form>
            </v-card-text>
        </v-card>
        
        <!-- Transfers List Card -->
        <v-card elevation="16">
            <v-card-title>
                Money Transfers for {{ selectedMonth }} {{ year }}
            </v-card-title>
            <v-card-text>
                <v-row>
                    <v-col cols="12" sm="6">
                        <v-autocomplete
                            label="Month"
                            v-model="selectedMonth"
                            :items="months"
                            density="comfortable"
                            variant="outlined"
                            :disabled="loading"
                        >
                        </v-autocomplete>
                    </v-col>
                </v-row>
                <v-row>
                    <v-col cols="12">
                        <v-table density="comfortable">
                            <thead>
                                <tr>
                                    <th class="text-left">
                                        Amount
                                    </th>
                                    <th class="text-left">
                                        Month
                                    </th>
                                    <th class="text-left">
                                        Type
                                    </th>
                                    <th class="text-left">
                                        Description
                                    </th>
                                    <th class="text-right">
                                        Actions
                                    </th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr v-if="!moneyTransfers[year] || !moneyTransfers[year][selectedMonth] || moneyTransfers[year][selectedMonth].length === 0">
                                    <td colspan="5" class="text-center">No transfers available for this period</td>
                                </tr>
                                <tr v-else v-for="(item, index) in currentMonthTransfers" :key="index">
                                    <td>{{ formatCurrency(item.amount) }}</td>
                                    <td>{{ item.month }}</td>
                                    <td>
                                        <v-chip
                                            :color="getTypeColor(item.type)"
                                            size="small"
                                            text-color="white"
                                        >
                                            {{ item.type }}
                                        </v-chip>
                                    </td>
                                    <td>{{ item.description }}</td>
                                    <td class="text-right">
                                        <v-btn icon size="small" color="primary" @click="editTransfer(item, index)">
                                            <v-icon>mdi-pencil</v-icon>
                                        </v-btn>
                                        <v-btn icon size="small" color="error" @click="deleteTransfer(item, index)">
                                            <v-icon>mdi-delete</v-icon>
                                        </v-btn>
                                    </td>
                                </tr>
                            </tbody>
                        </v-table>
                    </v-col>
                </v-row>
            </v-card-text>
        </v-card>
        
        <!-- Summary Card -->
        <v-row class="mt-4" v-if="hasTransfers">
            <v-col cols="12">
                <v-card elevation="4">
                    <v-card-title>Transfers Summary</v-card-title>
                    <v-card-text>
                        <v-row>
                            <v-col cols="12" sm="6" md="3">
                                <div class="text-subtitle-1">Total Transfers</div>
                                <div class="text-h5">{{ currentMonthTransfers.length }}</div>
                            </v-col>
                            <v-col cols="12" sm="6" md="3">
                                <div class="text-subtitle-1">Total Amount</div>
                                <div class="text-h5">{{ formatCurrency(totalAmount) }}</div>
                            </v-col>
                            <v-col cols="12" sm="6" md="3">
                                <div class="text-subtitle-1">Average Amount</div>
                                <div class="text-h5">{{ formatCurrency(averageAmount) }}</div>
                            </v-col>
                            <v-col cols="12" sm="6" md="3">
                                <div class="text-subtitle-1">By Type</div>
                                <div v-for="(count, type) in typeBreakdown" :key="type" class="d-flex align-center">
                                    <v-chip
                                        :color="getTypeColor(type)"
                                        size="small"
                                        text-color="white"
                                        class="mr-2 my-1"
                                    >
                                        {{ type }}
                                    </v-chip>
                                    <span>{{ count }}</span>
                                </div>
                            </v-col>
                        </v-row>
                    </v-card-text>
                </v-card>
            </v-col>
        </v-row>
        
        <!-- Edit Dialog -->
        <v-dialog v-model="editDialog" max-width="500px">
            <v-card>
                <v-card-title>Edit Money Transfer</v-card-title>
                <v-card-text>
                    <v-form ref="editForm">
                        <v-text-field
                            label="Amount"
                            v-model="editedItem.amount"
                            type="number"
                            prefix="$"
                            :rules="[v => !!v || 'Amount is required']"
                        ></v-text-field>
                        <v-autocomplete
                            label="Type"
                            v-model="editedItem.type"
                            :items="types"
                            :rules="[v => !!v || 'Type is required']"
                        ></v-autocomplete>
                        <v-text-field
                            label="Description"
                            v-model="editedItem.description"
                            :rules="[v => !!v || 'Description is required']"
                        ></v-text-field>
                    </v-form>
                </v-card-text>
                <v-card-actions>
                    <v-spacer></v-spacer>
                    <v-btn 
                        color="primary" 
                        variant="text" 
                        @click="saveEdit"
                        :disabled="loading"
                    >
                        Save
                    </v-btn>
                    <v-btn 
                        variant="text" 
                        @click="editDialog = false"
                        :disabled="loading"
                    >
                        Cancel
                    </v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>
        
        <!-- Confirmation Dialog -->
        <v-dialog v-model="confirmDialog" max-width="400px">
            <v-card>
                <v-card-title>Confirm Deletion</v-card-title>
                <v-card-text>
                    Are you sure you want to delete this transfer?
                </v-card-text>
                <v-card-actions>
                    <v-spacer></v-spacer>
                    <v-btn variant="text" @click="confirmDialog = false">Cancel</v-btn>
                    <v-btn 
                        color="error" 
                        variant="text" 
                        @click="confirmDelete"
                        :disabled="loading"
                    >
                        Delete
                    </v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>
    </v-container>
</template>

<script>
import ApiRequests from "@/api/requests";

export default {
    name: 'MoneyTransfers',
    props: {
        year: {
            type: String,
            required: true
        },
        years: {
            type: Array,
            default: () => []
        }
    },
    data() {
        return {
            loading: false,
            description: '',
            moneyTransfers: {},
            month: null,
            months: [
                'January', 'February', 'March', 'April', 
                'May', 'June', 'July', 'August', 
                'September', 'October', 'November', 'December'
            ],
            selectedMonth: null,
            transfer: null,
            type: null,
            types: ['Venmo', 'PayPal', 'Cash', 'Other'],
            typeColors: {
                'Venmo': '#3D95CE',
                'PayPal': '#169BD7',
                'Cash': '#21A038',
                'Other': '#757575'
            },
            editDialog: false,
            confirmDialog: false,
            editedItem: {
                amount: null,
                month: '',
                year: '',
                type: '',
                description: ''
            },
            editedIndex: -1,
            deleteItem: null,
            deleteIndex: -1
        }
    },

    computed: {
        currentMonthTransfers() {
            if (!this.moneyTransfers || 
                !this.moneyTransfers[this.year] || 
                !this.moneyTransfers[this.year][this.selectedMonth]) {
                return [];
            }
            return this.moneyTransfers[this.year][this.selectedMonth];
        },
        
        hasTransfers() {
            return this.currentMonthTransfers && this.currentMonthTransfers.length > 0;
        },
        
        totalAmount() {
            if (!this.hasTransfers) return 0;
            return this.currentMonthTransfers.reduce((sum, item) => sum + Number(item.amount), 0);
        },
        
        averageAmount() {
            if (!this.hasTransfers) return 0;
            return this.totalAmount / this.currentMonthTransfers.length;
        },
        
        typeBreakdown() {
            if (!this.hasTransfers) return {};
            
            const breakdown = {};
            this.currentMonthTransfers.forEach(item => {
                breakdown[item.type] = (breakdown[item.type] || 0) + 1;
            });
            
            return breakdown;
        },
        
        isFormValid() {
            return this.transfer && this.month && this.type && this.description;
        }
    },

    watch: {
        year(newValue) {
            this.updateData();
        }
    },

    mounted() {
        this.selectedMonth = this.months[new Date().getMonth()];
        this.month = this.months[new Date().getMonth()];
        
        if (Object.keys(this.moneyTransfers).length < 1) {
            this.loading = true;
            this.getMoneyTransfers();
        }
    },

    methods: {
        updateData() {
            this.month = this.months[new Date().getMonth()];
        },
        
        async getMoneyTransfers() {
            try {
                this.loading = true;
                const response = await ApiRequests.getMoneyTransfers();
                this.moneyTransfers = response.data;
            } catch (e) {
                console.error("Failed to fetch money transfers:", e);
                this.showError("Failed to load money transfers. Please try again.");
            } finally {
                this.loading = false;
            }
        },

        async addMoneyTransfer() {
            if (!this.isFormValid) return;
            
            try {
                this.loading = true;
                const data = {
                    'amount': this.transfer,
                    'month': this.month,
                    'year': this.year,
                    'type': this.type,
                    'description': this.description
                };
                
                const response = await ApiRequests.addMoneyTransfer(data);
                this.moneyTransfers = response.data;
                this.selectedMonth = this.month;
                
                this.description = '';
                this.transfer = null;
                this.type = null;
                
                if (this.$refs.transferForm) {
                    this.$refs.transferForm.reset();
                }
                
                this.month = this.months[new Date().getMonth()];
                
            } catch (e) {
                console.error("Failed to add money transfer:", e);
                this.showError("Failed to add money transfer. Please try again.");
            } finally {
                this.loading = false;
            }
        },
        
        editTransfer(item, index) {
            this.editedIndex = index;
            this.editedItem = Object.assign({}, item);
            this.editDialog = true;
        },
        
        async saveEdit() {
            if (!this.editedItem.amount || !this.editedItem.type || !this.editedItem.description) {
                this.showError("All fields are required");
                return;
            }
            
            try {
                this.loading = true;
                
                const data = {
                    id: this.editedItem.id,
                    amount: this.editedItem.amount,
                    type: this.editedItem.type,
                    description: this.editedItem.description,
                    month: this.editedItem.month,
                    year: this.editedItem.year
                };
                const response = await ApiRequests.updateMoneyTransfer(data);
                this.moneyTransfers = response.data;
                this.editDialog = false;
                
            } catch (e) {
                console.error("Failed to update money transfer:", e);
                this.showError("Failed to update money transfer. Please try again.");
                
            } finally {
                this.loading = false;
            }
        },    
            
        deleteTransfer(item, index) {
            this.deleteItem = item;
            this.deleteIndex = index;
            this.confirmDialog = true;
        },
        
        async confirmDelete() {
            try {
                this.loading = true;
                                
                
                const response = await ApiRequests.deleteMoneyTransfer(this.deleteItem.id);
                this.moneyTransfers = response.data;
                this.confirmDialog = false;
                this.deleteItem = null;
                this.deleteIndex = -1;
                
            } catch (e) {
                console.error("Failed to delete money transfer:", e);
                this.showError("Failed to delete money transfer. Please try again.");
            } finally {
                this.loading = false;
            }
        },
        
        getTypeColor(type) {
            return this.typeColors[type] || '#757575';
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
        }
    }
}
</script>

<style scoped>
.v-card {
    margin-bottom: 16px;
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