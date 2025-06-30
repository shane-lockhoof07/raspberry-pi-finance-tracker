<template>
    <v-tabs v-model="tab" bg-color="#ccccccff" height="56">
        <v-tab value="budget">Budget</v-tab>
        <v-tab value="schedule">Money Schedule</v-tab>
    </v-tabs>
    <v-progress-linear
        :active="budgetLoading"
        :indeterminate="budgetLoading"
        color="#FFFFFF"
    ></v-progress-linear>
    <v-container fluid>
        <v-window v-model="tab">
            <v-window-item value="budget">
                <v-row>
                    <v-col cols="12" md="6">
                        <v-card class="mb-6" variant="flat">
                            <v-card-title class="d-flex justify-space-between">
                                <span>Monthly Budget: ${{ formatCurrency(totalBudget) }}</span>
                                <v-btn icon="mdi-plus" @click="addBudgetDialog = true"></v-btn>
                            </v-card-title>
                            <v-card-text>
                                <PieChart
                                    v-if="hasBudget && !budgetLoading"
                                    :categories="chartCategories"
                                    :values="chartValues"
                                    :colors="chartColors"
                                    chartType="doughnut"
                                    @slice-click="handleChartClick"
                                />
                                <v-alert
                                    v-else-if="!budgetLoading && !hasBudget"
                                    type="info"
                                    text="No budget added yet. Add your first expense to see the chart."
                                ></v-alert>
                                <div v-else-if="budgetLoading" class="d-flex justify-center align-center" style="height: 300px">
                                    <v-progress-circular indeterminate color="primary"></v-progress-circular>
                                </div>
                            </v-card-text>
                        </v-card>          
                    </v-col>
                    
                    <!-- Management Column -->
                    <v-col cols="12" md="6">
                        <!-- Budget List -->
                        <v-card>
                            <v-card-title>
                                Budget List
                            </v-card-title>
                            <v-card-text>
                                <v-text-field
                                v-model="search"
                                append-icon="mdi-magnify"
                                label="Search"
                                single-line
                                hide-details
                                dense
                                ></v-text-field>
                                <v-data-table
                                    :headers="headers"
                                    :items="budget"
                                    :search="search"
                                    :items-per-page="-1"
                                    item-key="key"
                                    :no-data-text="'No budget found. Add an expense to get started.'"
                                    :loading-text="'Loading budget...'"
                                    :loading="budgetLoading"
                                    :sort-by="['value']"
                                    :sort-desc="[true]"
                                    hide-default-footer
                                    hide-default-header
                                >
                                    <template v-slot:item.value="{ item }">
                                    ${{ formatCurrency(item.value) }}
                                    </template>
                                    <template v-slot:item.percentage="{ item }">
                                    {{ calculatePercentage(item.value) }}%
                                    </template>
                                    <template v-slot:item.category_color="{ item }">
                                    <v-chip
                                        :color="getCategoryColor(item.key)"
                                        small
                                        class="ml-0 mr-2"
                                    ></v-chip>
                                    </template>
                                    <template v-slot:item.actions="{ item }">
                                    <v-tooltip bottom>
                                        <template v-slot:activator="{ on, attrs }">
                                        <v-icon 
                                            small 
                                            class="mr-2" 
                                            v-bind="attrs"
                                            @click="editItem(item)"
                                        >
                                            mdi-pencil
                                        </v-icon>
                                        </template>
                                        <span>Edit</span>
                                    </v-tooltip>
                                    <v-tooltip bottom>
                                        <template v-slot:activator="{ on, attrs }">
                                        <v-icon 
                                            small 
                                            v-bind="attrs"
                                            @click="deleteItem(item)"
                                        >
                                            mdi-delete
                                        </v-icon>
                                        </template>
                                        <span>Delete</span>
                                    </v-tooltip>
                                    </template>
                                </v-data-table>
                            </v-card-text>
                        </v-card>
                    </v-col>
                </v-row>
            </v-window-item>
            <v-window-item value="schedule">
                <MoneySchedule />
            </v-window-item>
        </v-window>
        <v-dialog v-model="detailDialog" max-width="500">
            <v-card v-if="selectedBudget" align="center">
                <v-card-title class="headline">
                    <v-chip
                    :color="getCategoryColor(selectedBudget.key)"
                    class="mr-2"
                    ></v-chip>
                    {{ selectedBudget.key }} Details
                </v-card-title>
                <v-card-text>
                    <v-row>
                        <v-col cols="12" md="4">
                            Amount: ${{ formatCurrency(selectedBudget.value) }}
                        </v-col>
                        <v-col cols="12" md="4">
                            Percentage of Total: {{ calculatePercentage(selectedBudget.value) }}%
                        </v-col>
                        <v-col cols="12" md="4">
                            Total Budget: ${{ formatCurrency(totalBudget) }}
                        </v-col>
                    </v-row>
                </v-card-text>
                <v-card-actions>
                    <v-spacer></v-spacer>
                    <v-btn color="primary" text @click="editItem(selectedBudget)">Edit</v-btn>
                    <v-btn color="error" text @click="deleteSelectedBudget">Delete</v-btn>
                    <v-btn text @click="detailDialog = false">Close</v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>
        <v-dialog v-model="groupCategoriesDialog" max-width="700">
            <v-card>
                <v-card-title>
                    Grouped Categories
                </v-card-title>
                <v-card-text>
                    <v-row v-for="item in smallCategoriesFormatted">
                        <v-col cols="12">
                            <v-card align="center" variant="flat">
                                <v-card-title>
                                    {{item.key}}
                                </v-card-title>
                                <v-card-text>
                                    <v-row>
                                        <v-col cols="12" md="4">
                                            Amount: ${{ formatCurrency(item.value) }}
                                        </v-col>
                                        <v-col cols="12" md="4">
                                            Percentage of Total: {{ calculatePercentage(item.value) }}%
                                        </v-col>
                                        <v-col cols="12" md="4">
                                            Total Budget: ${{ formatCurrency(totalBudget) }}
                                        </v-col>
                                    </v-row>
                                </v-card-text>
                                <v-card-actions>
                                    <v-spacer></v-spacer>
                                    <v-btn color="primary" text @click="editItem(item)">Edit</v-btn>
                                    <v-btn color="error" text @click="deleteItem(item)">Delete</v-btn>
                                </v-card-actions>
                            </v-card>
                        </v-col>
                    </v-row>
                </v-card-text>
                <v-card-actions>
                    <v-spacer></v-spacer>
                    <v-btn text @click="groupCategoriesDialog = false">Close</v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>
        <v-dialog v-model="editDialog" max-width="500">
            <v-card>
            <v-card-title>Edit {{editedItem.key}} Budget</v-card-title>
            <v-card-text>
                <v-form ref="editForm">
                <v-text-field
                    v-model.number="editedItem.value"
                    label="Amount"
                    type="number"
                    prefix="$"
                    :rules="amountRules"
                ></v-text-field>
                </v-form>
            </v-card-text>
            <v-card-actions>
                <v-spacer></v-spacer>
                <v-btn color="primary" text @click="saveEdit" :loading="formSubmitting">Save</v-btn>
                <v-btn text @click="cancelEdit">Cancel</v-btn>
            </v-card-actions>
            </v-card>
        </v-dialog>
        <v-dialog v-model="addBudgetDialog" max-width="400">
            <v-card class="mb-6">
                <v-card-title>Add Budget</v-card-title>
                <v-card-text>
                    <v-form @submit.prevent="addBudget" ref="form">
                    <v-text-field
                        v-model="newCategory"
                        label="Budget Category"
                        :rules="categoryRules"
                        autocapitalize="words"
                        trim
                    ></v-text-field>
                    
                    <v-text-field
                        v-model.number="newAmount"
                        label="Amount"
                        type="number"
                        :rules="amountRules"
                        prefix="$"
                    ></v-text-field>
                    
                    <v-btn 
                        color="primary" 
                        type="submit" 
                        class="mt-4"
                        :disabled="!isFormValid || budgetLoading"
                        :loading="formSubmitting"
                    >
                        Add Budget
                    </v-btn>
                    </v-form>
                </v-card-text>
            </v-card>
        </v-dialog>
        <v-dialog v-model="confirmDialog" max-width="400">
            <v-card>
            <v-card-title>Confirm Action</v-card-title>
            <v-card-text>{{ confirmMessage }}</v-card-text>
            <v-card-actions>
                <v-spacer></v-spacer>
                <v-btn text @click="confirmDialog = false">Cancel</v-btn>
                <v-btn 
                color="error" 
                text 
                @click="confirmAction"
                :loading="formSubmitting"
                >
                Confirm
                </v-btn>
            </v-card-actions>
            </v-card>
        </v-dialog>
        <v-snackbar
            v-model="snackbar.show"
            :color="snackbar.color"
            :timeout="snackbar.timeout"
            bottom
            right
        >
            {{ snackbar.text }}
            <template v-slot:action="{ attrs }">
                <v-btn
                    text
                    v-bind="attrs"
                    @click="snackbar.show = false"
                >
                    Close
                </v-btn>
            </template>
        </v-snackbar>
    </v-container>
</template>

<script>
import ApiRequests from "@/api/requests";
import PieChart from '@/components/PieChart.vue';
import MoneySchedule from "@/components/MoneySchedule.vue";

export default {
    name: 'BudgetTracker',
    components: {
        PieChart,
        MoneySchedule
    },
    data() {
        return {
            addBudgetDialog: false,
            budget: [],
            budgetLoading: false,
            formSubmitting: false,
            tab: "budget",
            baseColors: [
            '#c5c7ff', '#aae4bb', '#e198a8', '#80e1e2', '#ffcbf5', '#87e3ff', '#a0b187', '#b1a5d1', 
            '#ffd2bc', '#d0f7ff', '#f2e0ff', '#fffae0', '#8eb0c8', '#b2a8b4', '#fffbfb', '#a4aea4',
            ],
            categoryColors: {},

            headers: [
                { text: 'Color', value: 'category_color', sortable: false, width: '50px' },
                { text: 'Category', value: 'key' },
                { text: 'Amount', value: 'value' },
                { text: 'Percentage', value: 'percentage', sortable: false },
                { text: 'Actions', value: 'actions', sortable: false, align: 'end' }
            ],
            search: '',
            
            detailDialog: false,
            editDialog: false,
            confirmDialog: false,
            groupCategoriesDialog: false,
            confirmMessage: '',
            confirmCallback: null,
            selectedBudget: null,
            editedItem: { key: '', value: 0 },
            editedIndex: -1,
            newCategory: '',
            newAmount: null,
            categoryRules: [
                v => !!v.trim() || 'Category is required',
                v => v.length <= 30 || 'Category name must be less than 30 characters'
            ],
            amountRules: [
                v => !!v || 'Amount is required',
                v => v > 0 || 'Amount must be greater than 0',
                v => v <= 1000000 || 'Amount must be less than $1,000,000'
            ],
            snackbar: {
                show: false,
                text: '',
                color: 'success',
                timeout: 3000
            }
        };
    },
    computed: {
        validBudgetItems() {
            return this.budget.filter(item => item.value > 0);
        },
        
        sortedBudgetItems() {
            return [...this.validBudgetItems].sort((a, b) => b.value - a.value);
        },

        smallCategories() {
            return this.validBudgetItems
                .filter(item => item.value < 300)
                .sort((a, b) => b.value - a.value);
        },

        largeCategories() {
            return this.validBudgetItems
                .filter(item => item.value >= 300)
                .sort((a, b) => b.value - a.value);
        },
        
        groupCategoriesTotal() {
            return this.smallCategories.reduce((sum, item) => sum + item.value, 0);
        },
        
        smallCategoriesFormatted() {
            return this.smallCategories.map(item => ({
                ...item,
                formattedValue: `$${this.formatCurrency(item.value)}`,
                percentage: this.calculatePercentage(item.value)
            }));
        },
        
        chartCategories() {
            const categories = [...this.largeCategories.map(item => item.key)];
            
            if (this.smallCategories.length > 0) {
                categories.push('Grouped');
            }
            
            return categories;
        },
        
        chartValues() {
            const values = [...this.largeCategories.map(item => item.value)];
            
            if (this.smallCategories.length > 0) {
                values.push(this.groupCategoriesTotal);
            }
            
            return values;
        },
        
        chartColors() {
            const colors = this.chartCategories.map(category => {
                if (category === 'Grouped') {
                    return '#607D8B'; 
                }
                return this.getCategoryColor(category);
            });
            
            return colors;
        },
        
        hasBudget() {
            return this.validBudgetItems.length > 0;
        },
        
        totalBudget() {
            return this.validBudgetItems.reduce((sum, item) => sum + item.value, 0);
        },
        
        averageBudget() {
            return this.hasBudget ? (this.totalBudget / this.validBudgetItems.length).toFixed(2) : '0.00';
        },
        
        highestBudget() {
            if (!this.hasBudget) return { key: 'None', value: 0 };
            return this.validBudgetItems.reduce((max, item) => 
                item.value > max.value ? item : max, { value: -Infinity });
        },
        
        lowestBudget() {
            if (!this.hasBudget) return { key: 'None', value: 0 };
            return this.validBudgetItems.reduce((min, item) => 
                item.value < min.value ? item : min, { value: Infinity });
        },
        
        isFormValid() {
            return this.newCategory && this.newCategory.trim() && this.newAmount > 0;
        }
    },
    
    watch: {
        budget: {
            handler() {
                this.updateCategoryColors();
            },
            deep: true
        }
    },

    created() {
        this.fetchBudgetData();
    },

    methods: {
        async fetchBudgetData() {
            this.budgetLoading = true;
            
            try {
                const response = await ApiRequests.getBudget();
                this.budget = response.data.sort((a, b) => b.value - a.value);
                this.updateCategoryColors();
            } catch (error) {
                this.showNotification('Failed to load budget data. Please try again.', 'error');
                console.error("Failed to fetch budget data:", error);
            } finally {
                this.budgetLoading = false;
            }
        },
        
        async saveBudgetItem(item) {
            // This would be implemented to call the API
            // Example:
            // try {
            //     const response = await ApiRequests.addBudgetItem(item);
            //     return response.data;
            // } catch (error) {
            //     throw error;
            // }
            
            // For now, we'll just simulate success
            return Promise.resolve(item);
        },
        
        async updateBudgetItem(item) {
            try {
                const response = await ApiRequests.updateBudgetItem(item);
                return response.data;
            } catch (error) {
                throw error;
            }
        },
        
        async deleteBudgetItem(item) {
            try {
                const response = await ApiRequests.deleteBudgetItem(item.key);
                return response.data;
            } catch (error) {
                throw error;
            }
        },

        updateCategoryColors() {
            const categories = this.budget.map(item => item.key);
            
            categories.forEach((category, index) => {
                if (!this.categoryColors[category]) {
                    this.categoryColors[category] = index < this.baseColors.length
                        ? this.baseColors[index]
                        : this.generateRandomColor();
                }
            });
        },
        
        getCategoryColor(category) {
            return this.categoryColors[category] || this.generateRandomColor();
        },
        
        generateRandomColor() {
            return '#' + Math.floor(Math.random()*16777215).toString(16).padStart(6, '0');
        },
        
        handleChartClick(data) {
            if (!data || data.index === undefined) return;
            
            const category = data.category;
            
            if (category === 'Grouped') {
                this.groupCategoriesDialog = true;
                return;
            }
            
            const selectedBudget = this.budget.find(exp => exp.key === category);
            
            if (selectedBudget) {
                this.selectedBudget = selectedBudget;
                this.detailDialog = true;
            }
        },
        
        async addBudget() {
            if (!this.isFormValid) return;
            
            const category = this.newCategory.trim();
            
            const existingIndex = this.budget.findIndex(item => 
                item.key.toLowerCase() === category.toLowerCase());
                
            if (existingIndex !== -1) {
                this.confirmMessage = `Category "${category}" already exists. Update its value?`;
                this.confirmCallback = async () => {
                    this.formSubmitting = true;
                    
                    try {
                        const updatedItem = {
                            key: this.budget[existingIndex].key,
                            value: this.newAmount
                        };
                        
                        await this.updateBudgetItem(updatedItem);
                        
                        this.budget[existingIndex].value = this.newAmount;
                        
                        this.showNotification('Budget updated successfully', 'success');
                    } catch (error) {
                        this.showNotification('Failed to update budget', 'error');
                        console.error("Failed to update budget:", error);
                    } finally {
                        this.formSubmitting = false;
                        this.confirmDialog = false;
                        this.resetForm();
                    }
                };
                this.confirmDialog = true;
            } else {
                this.formSubmitting = true;
                
                try {
                    const newItem = {
                        key: category,
                        value: this.newAmount
                    };
                    try {
                        const response = await ApiRequests.addBudgetItem(newItem);
                        this.showNotification('Budget added successfully', 'success');
                        this.budget.push(newItem);
                        return response.data;
                    } catch (error) {
                        console.log(error)
                        throw error;
                    }
                } catch (error) {
                    this.showNotification('Failed to add budget', 'error');
                    console.error("Failed to add budget:", error);
                } finally {
                    this.formSubmitting = false;
                    this.resetForm();
                }
            }
        },
        
        editItem(item) {
            this.editedIndex = this.budget.indexOf(item);
            this.editedItem = Object.assign({}, item);
            this.editDialog = true;
            this.detailDialog = false; 
        },
        
        async saveEdit() {
            if (!this.editedItem.key.trim() || this.editedItem.value <= 0) return;
            
            const category = this.editedItem.key.trim();
            
            const duplicateIndex = this.budget.findIndex((item, idx) => 
                idx !== this.editedIndex && 
                item.key.toLowerCase() === category.toLowerCase());
                
            if (duplicateIndex !== -1) {
                this.confirmMessage = `Angroup expense with category "${category}" already exists. This will overwrite it. Continue?`;
                this.confirmCallback = async () => {
                    this.formSubmitting = true;
                    
                    try {
                        await this.updateBudgetItem(this.editedItem);
                        
                        this.budget.splice(duplicateIndex, 1);
                        
                        this.budget[this.editedIndex].key = category;
                        this.budget[this.editedIndex].value = this.editedItem.value;
                        
                        this.showNotification('Budget updated successfully', 'success');
                    } catch (error) {
                        this.showNotification('Failed to update budget', 'error');
                        console.error("Failed to update budget:", error);
                    } finally {
                        this.formSubmitting = false;
                        this.confirmDialog = false;
                        this.editDialog = false;
                    }
                };
                this.confirmDialog = true;
            } else {
                this.formSubmitting = true;
                
                try {
                    await this.updateBudgetItem(this.editedItem);
                    
                    this.budget[this.editedIndex].key = category;
                    this.budget[this.editedIndex].value = this.editedItem.value;
                    
                    this.showNotification('Budget updated successfully', 'success');
                } catch (error) {
                    this.showNotification('Failed to update budget', 'error');
                    console.error("Failed to update budget:", error);
                } finally {
                    this.formSubmitting = false;
                    this.editDialog = false;
                }
            }
        },
        
        cancelEdit() {
            this.editDialog = false;
            this.editedItem = { key: '', value: 0 };
            this.editedIndex = -1;
        },
        
        deleteItem(item) {
            const index = this.budget.indexOf(item);
            
            this.confirmMessage = `Are you sure you want to delete "${item.key}"?`;
            this.confirmCallback = async () => {
                this.formSubmitting = true;
                
                try {
                    await this.deleteBudgetItem(item);
                    
                    this.budget.splice(index, 1);
                    
                    if (this.selectedBudget && this.selectedBudget.key === item.key) {
                        this.detailDialog = false;
                    }
                    
                    this.showNotification('Budget deleted successfully', 'success');
                } catch (error) {
                    this.showNotification('Failed to delete budget', 'error');
                    console.error("Failed to delete budget:", error);
                } finally {
                    this.formSubmitting = false;
                    this.confirmDialog = false;
                }
            };
            this.confirmDialog = true;
        },
        
        deleteSelectedBudget() {
            if (!this.selectedBudget) return;
            
            const index = this.budget.indexOf(this.selectedBudget);
            if (index !== -1) {
                this.confirmMessage = `Are you sure you want to delete "${this.selectedBudget.key}"?`;
                this.confirmCallback = async () => {
                    this.formSubmitting = true;
                    
                    try {
                        await this.deleteBudgetItem(this.selectedBudget);
                        
                        this.budget.splice(index, 1);
                        
                        this.showNotification('Budget deleted successfully', 'success');
                    } catch (error) {
                        this.showNotification('Failed to delete budget', 'error');
                        console.error("Failed to delete budget:", error);
                    } finally {
                        this.formSubmitting = false;
                        this.confirmDialog = false;
                        this.detailDialog = false;
                    }
                };
                this.confirmDialog = true;
            }
        },
        
        calculatePercentage(value) {
            return this.totalBudget ? ((value / this.totalBudget) * 100).toFixed(1) : '0.0';
        },
        
        formatCurrency(value) {
            return parseFloat(value).toLocaleString('en-US', { 
                minimumFractionDigits: 0,
                maximumFractionDigits: 0
            });
        },
        
        resetForm() {
            this.newCategory = '';
            this.newAmount = null;
            if (this.$refs.form) {
                this.$refs.form.reset();
            }
        },
        
        confirmAction() {
            if (typeof this.confirmCallback === 'function') {
                this.confirmCallback();
            } else {
                this.confirmDialog = false;
            }
        },
        
        showNotification(text, color = 'success') {
            this.snackbar.text = text;
            this.snackbar.color = color;
            this.snackbar.show = true;
        }
    }
};
</script>

<style scoped>
.v-card {
border-radius: 8px;
box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.v-card__title {
font-weight: 700;
}

.headline {
border-bottom: 1px solid rgba(0, 0, 0, 0.12);
}

.v-data-table ::v-deep .v-data-table__wrapper {
overflow-x: auto;
padding-top: -30px;
}

/* Responsive adjustments */
@media (max-width: 600px) {
.v-card {
    margin-bottom: 16px;
}
}
</style>