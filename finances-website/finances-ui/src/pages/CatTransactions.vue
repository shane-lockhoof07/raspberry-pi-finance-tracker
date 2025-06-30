<template>
    <v-row v-if="error">
        <v-col>
            <v-alert
                dense
                type="error"
                border="left"
            >
                {{ error }}
                <div class="mt-2">
                    <v-btn small @click="refreshTransactions">Try Again</v-btn>
                </div>
            </v-alert>
        </v-col>
    </v-row>
    <v-container fluid v-if="newTransactions">
        <v-row v-if="loadingTransactions">
            <v-col class="text-center">
                <v-progress-circular
                    indeterminate
                    color="primary"
                    size="64"
                ></v-progress-circular>
                <div class="mt-3">Loading transactions...</div>
            </v-col>
        </v-row>
        <v-row>
            Please categorize the following transaction:
        </v-row>
        <v-row justify="center">
            <v-col cols="12" md="10" lg="10">
                <v-card rounded="lg" elevation="16">
                    <v-card-text>
                        <v-table v-if="currentTransaction">
                            <thead>
                                <tr>
                                    <th class="text-center">Date</th>
                                    <th class="text-center">Vendor</th>
                                    <th class="text-center">Amount</th>
                                    <th class="text-center">Card</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td class="text-center">{{ formatDate(currentTransaction.date) }}</td>
                                    <td class="text-center">{{ currentTransaction.vendor }}</td>
                                    <td class="text-center">$ {{ currentTransaction.amount }}</td>
                                    <td class="text-center">{{ formatCardIssuer(currentTransaction.card_issuer) }}</td>
                                </tr>
                            </tbody>
                        </v-table>
                    </v-card-text>
                </v-card>
            </v-col>
        </v-row>
        <v-row>
            <v-col v-for="category in orderedCategories" 
                   :key="category"
                   cols="6" 
                   md="3" 
                   sm="4">
                <v-btn size="x-large" rounded="xl" block @click="updateCategory(category)">{{ category }}</v-btn>
            </v-col>
        </v-row>
    </v-container>
    <v-container fluid v-if="redoTransactions && !newTransactions">
        <v-row>
            The following transaction could not be parsed, please fill out the relevant information for this transaction.
        </v-row>
        <v-row justify="center">
            <v-col cols="12" md="10" lg="10">
                <v-card rounded="lg" elevation="16">
                    <v-card-text v-if="currentTransaction">
                        <v-row justify="center">
                            <v-table>
                                <tbody>
                                    <tr>
                                        <td v-for="item in currentTransaction" style="font-size: 24px;">{{item}}</td>
                                    </tr>
                                </tbody>
                            </v-table>
                        </v-row>
                        <v-row>
                            <v-col cols="12" md="3">
                                <v-text-field
                                    label="Date (DD-MM-YYYY)"
                                    v-model="misformattedDate"
                                ></v-text-field>
                            </v-col>
                            <v-col cols="12" md="3">
                                <v-text-field
                                    label="Amount"
                                    v-model="misformattedAmount"
                                ></v-text-field>
                            </v-col>  
                            <v-col cols="12" md="3">
                                <v-autocomplete
                                    label="Category"
                                    v-model="misformattedCat"
                                    :items="orderedCategories"
                                ></v-autocomplete>
                            </v-col>  
                            <v-col cols="12" md="3">
                                <v-text-field
                                    label="Vendor"
                                    v-model="misformattedVendor"
                                ></v-text-field>
                            </v-col>                        
                        </v-row>
                        <v-row v-if="errorText" justify="center">
                            ERROR!! {{ errorText }}
                        </v-row>
                    </v-card-text>
                    <v-card-actions>
                        <v-btn
                            block
                            @click="addTransaction()"
                        >Add Transaction</v-btn>
                    </v-card-actions>
                </v-card>
            </v-col>
        </v-row>
    </v-container>
    <v-container fluid v-else-if="completedAll">
        <v-row>
            <v-col class="text-center">
                <h3>All transactions have been categorized!</h3>
            </v-col>
        </v-row>
    </v-container>
    <v-btn size="x-large" rounded="xl" block @click="resetTransactions" v-if="newTransactions">Reset</v-btn>
</template>

<script>
import ApiRequests from "@/api/requests";

export default {
    data() {
        return {
            categories: {},
            newTransactions: false,
            redoTransactions: false,
            orderedCategories: [],
            errorText: null,
            uncategorizedTransactions: [],
            loaduingTransactions: false,
            error: null,
            misformattedDate: null,
            misformattedAmount: null,
            misformattedCat: null,
            misformattedVendor: null,
            misformattedTransactions: [],
            currentTransactionIndex: 0,
            completedAll: false,
            tableHeaders: [
                {key: 'date', title: 'Date'}, 
                {key: 'vendor', title: 'Vendor'}, 
                {key: 'amount', title: 'Amount'}, 
                {key: 'card_issuer', title: 'Card'}
            ]
        }
    },

    computed: {
        currentTransaction() {
            if (this.uncategorizedTransactions.length > this.currentTransactionIndex) {
                return this.uncategorizedTransactions[this.currentTransactionIndex];
            }
            if (this.misformattedTransactions.length > this.currentTransactionIndex) {
                return this.misformattedTransactions[this.currentTransactionIndex];
            }
            this.redoTransactions = false;
            this.newTransactions = false;
            this.completedAll = true;
            return null;
        }
    },

    mounted() {
        this.sortedCategories();
        this.getNewTransactions();
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

        async getNewTransactions() {
            try {
                this.loadingTransactions = true;
                this.error = null;
                console.log("Fetching uncategorized transactions...");
                
                const response = await ApiRequests.getNewTransactions();
                console.log("Transaction response:", response.data);
                
                // Check if there's an error message in the response
                if (response.data.error) {
                    console.error("API returned an error:", response.data.error);
                    this.error = `Server error: ${response.data.error}`;
                    this.loadingTransactions = false;
                    return;
                }
                
                // Reset state
                this.uncategorizedTransactions = [];
                this.misformattedTransactions = [];
                this.currentTransactionIndex = 0;
                this.completedAll = false;
                this.newTransactions = false;
                this.redoTransactions = false;
                
                // Update with new data
                this.uncategorizedTransactions = response.data.transactions || [];
                this.misformattedTransactions = response.data.misformatted_transactions || [];
                
                console.log(`Found ${this.uncategorizedTransactions.length} uncategorized transactions`);
                console.log(`Found ${this.misformattedTransactions.length} misformatted transactions`);
                
                // Determine which view to show
                if (this.uncategorizedTransactions.length > 0) {
                    this.newTransactions = true;
                    this.redoTransactions = false;
                } else if (this.misformattedTransactions.length > 0) {
                    this.redoTransactions = true;
                    this.newTransactions = false;
                } else {
                    this.completedAll = true;
                }
                
                this.loadingTransactions = false;
                return response.data;
            } catch (e) {
                this.loadingTransactions = false;
                console.error("Failed to get transactions", e);
                this.error = `Error: ${e.message || "Failed to load transactions"}`;
                this.completedAll = false;
                return null;
            }
        },

        async updateCategory(category) {
            if (!this.currentTransaction) return;

            try {
                this.currentTransaction.category = category
                await ApiRequests.updateTransactionCategory(this.currentTransaction);
                
                this.currentTransactionIndex++;
                
                if (this.currentTransactionIndex >= this.uncategorizedTransactions.length) {
                    if (this.misformattedTransactions.length > 0) {
                        this.currentTransactionIndex = 0;
                        this.newTransactions = false;
                        this.redoTransactions = true;  
                    } else {
                        this.newTransactions = false;
                        this.completedAll = true; 
                    }
                }
            } catch (e) {
                console.log("Failed to update category", e);
            }
        },

        async addTransaction() {
            let dateValue = "";
            let floatValue = 0;
            if (!this.misformattedDate || !this.misformattedAmount || !this.misformattedCat || !this.misformattedVendor) {
                this.errorText = "Please fill out all fields."
            } else {
                dateValue = this.convertToDateFormat(this.misformattedDate)
                floatValue = parseFloat(this.misformattedAmount);
                if (dateValue == "" && !floatValue) {
                    this.errorText = "Please enter the date in the format DD-MM-YYYY and enter a number for the amount."
                } else if (dateValue == "") {
                    this.errorText = "Please enter the date in the format DD-MM-YYYY."
                } else if (!floatValue) {
                    this.errorText = "Please enter a number for the amount."
                }
            }

            try {
                var data = {
                    "reference_data": this.misformattedTransactions[this.currentTransactionIndex],
                    "date": dateValue,
                    "amount": floatValue,
                    "category": this.misformattedCat,
                    "vendor": this.misformattedVendor,
                    "index": this.currentTransactionIndex
                }
                const response = await ApiRequests.addTransaction(data);
                this.misformattedTransactions = response.data;
                this.currentTransactionIndex = 0;
                this.errorText = null
            } catch (e) {
                console.log("Failed to update category", e);
            }
        },

        resetTransactions() {
            this.newTransactions = false;
            this.currentTransactionIndex = 0;
        },

        formatDate(dateString) {
            if (!dateString) return '';
            
            const date = new Date(dateString);
            if (isNaN(date.getTime())) return dateString;
            
            const options = { 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric' 
            };
            
            return date.toLocaleDateString('en-US', options);
        },


        formatCardIssuer(cardIssuer) {
            if (!cardIssuer) return '';
            
            if (cardIssuer.includes('capone')) {
                cardIssuer = cardIssuer.replace('capone', 'Capital One');
            }
            const withSpaces = cardIssuer.replace(/_/g, ' ');
            
            return withSpaces
                .split(' ')
                .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
                .join(' ');
        },

        convertToDateFormat(dateString) {
            const date = new Date(dateString);          
            if (isNaN(date.getTime())) {
                return "";
            }
            
            const day = String(date.getDate()).padStart(2, '0');
            const month = String(date.getMonth() + 1).padStart(2, '0'); 
            const year = date.getFullYear();
            
            return `${day}-${month}-${year}`;
        }
    }
}
</script>