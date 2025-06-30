<template>
    <div>
      <v-card>
        <v-row justify="end">
          <v-col cols="5" class="text-right">
            <v-btn
              color="green-darken-3"
              @click="openBalanceDialog"
              size="large"
              rounded="xs"
              block
            >
              <h5>Current Balance: </h5> 
              <h3>{{ formatCurrency(bankBalance) }}</h3>
            </v-btn>
          </v-col>
        </v-row>
  
        <v-data-table
          v-if="!loading"
          :headers="headers"
          hide-default-header
          hide-default-footer
          :items="processedData"
          :sort-by="['date']"
          :sort-desc="[false]"
          :items-per-page="-1"
          class="elevation-1"
          :custom-sort="() => processedData"
        >
          <template v-slot:item="{ item, columns }">
            <tr @click="openEditDialog(item)">
              <td v-for="(column, index) in columns" :key="index">
                <span v-if="column.key === 'date'">
                  {{ formatDate(item.date) }}
                </span>
                <span v-else-if="column.key === 'net'" :class="{ 'negative-value-text': item.netValue < 0 }">
                  {{ item[column.key] }}
                </span>
                <span v-else>
                  {{ item[column.key] }}
                </span>
              </td>
            </tr>
          </template>
        </v-data-table>
        
        <v-card-actions class="d-flex pa-2 justify-center">
          <v-btn
            color="primary"
            @click="openAddDialog"
            prepend-icon="mdi-plus"
          >
            Add Transaction
          </v-btn>
        </v-card-actions>
      </v-card>
      <v-dialog v-model="balanceDialog" max-width="500px">
        <v-card>
          <v-card-title>
            <span class="text-h5">Update Bank Balance</span>
          </v-card-title>
  
          <v-card-text>
            <v-container>
              <v-row>
                <v-col cols="12">
                  <v-text-field
                    v-model.number="editedBalance"
                    label="Current Bank Balance"
                    prefix="$"
                    type="number"
                    outlined
                  ></v-text-field>
                </v-col>
              </v-row>
            </v-container>
          </v-card-text>
  
          <v-card-actions>
            <v-col cols="12" md="6" sm="6">
                <v-btn color="red-darken-1" text @click="closeBalanceDialog" block>Cancel</v-btn>
            </v-col>
            <v-col cols="12" md="6" sm="6">
                <v-btn color="green-darken-1" text @click="saveBalance" block>Save</v-btn>
            </v-col>
          </v-card-actions>
        </v-card>
      </v-dialog>
      <v-dialog v-model="editDialog" max-width="600px">
        <v-card>
          <v-card-title>
            <span class="text-h5">Edit Transaction</span>
          </v-card-title>
  
          <v-card-text>
            <v-container>
              <v-row>
                <v-col cols="12" sm="4" md="4">
                    <v-text-field
                    v-model="editedItem.date"
                    label="Date"
                    prepend-icon="mdi-calendar"
                    ></v-text-field>
                </v-col>
                <v-col cols="12" sm="4" md="4">
                  <v-text-field
                    v-model="editedItem.source"
                    label="Source"
                  ></v-text-field>
                </v-col>
                <v-col cols="12" sm="4" md="4">
                  <v-text-field
                    v-model.number="editedItem.amount"
                    label="Amount"
                    prefix="$"
                    type="number"
                  ></v-text-field>
                </v-col>
              </v-row>
            </v-container>
          </v-card-text>
  
          <v-card-actions>
            <v-col cols="12" md="6" sm="6">
                <v-btn color="red-darken-1" text @click="closeDialog" block>Cancel</v-btn>
            </v-col>
            <v-col cols="12" md="6" sm="6">
                <v-btn color="green-darken-1" text @click="saveItem" block>Save</v-btn>
            </v-col>
          </v-card-actions>
        </v-card>
      </v-dialog>
      <v-dialog v-model="addDialog" max-width="600px">
        <v-card>
          <v-card-title>
            <span class="text-h5">Add New Transaction</span>
          </v-card-title>
  
          <v-card-text>
            <v-container>
              <v-row>
                <v-col cols="12" sm="4" md="4">
                    <v-text-field
                    v-model="newItem.date"
                    label="Date"
                    prepend-icon="mdi-calendar"
                    ></v-text-field>
                </v-col>
                <v-col cols="12" sm="4" md="4">
                  <v-text-field
                    v-model="newItem.source"
                    label="Source"
                  ></v-text-field>
                </v-col>
                <v-col cols="12" sm="4" md="4">
                  <v-text-field
                    v-model.number="newItem.amount"
                    label="Amount"
                    prefix="$"
                    type="number"
                  ></v-text-field>
                </v-col>
              </v-row>
            </v-container>
          </v-card-text>
  
          <v-card-actions>
            <v-col cols="12" md="6" sm="6">
                <v-btn color="red-darken-1" text @click="closeAddDialog" block>Cancel</v-btn>
            </v-col>
            <v-col cols="12" md="6" sm="6">
                <v-btn color="green-darken-1" text @click="addItem" block>Add</v-btn>
            </v-col>
          </v-card-actions>
        </v-card>
      </v-dialog>
    </div>
  </template>
  
  <script>
  import ApiRequests from '@/api/requests';
  
  export default {
    name: 'MoneySchedule',
    data() {

      const today = new Date().toISOString().split('T')[0];
      
      return {
        loading: false,
        bankBalance: null,
        editedBalance: null,
        balanceDialog: false,
        dateMenu: false,
        addDateMenu: false,
        editDialog: false,
        addDialog: false,
        editedIndex: -1,
        editedItem: {
          id: '',
          date: '',
          source: '',
          amount: 0,
        },
        newItem: {
          date: today, 
          source: '',
          amount: 0,
        },
        defaultItem: {
          id: '',
          date: '',
          source: '',
          amount: 0,
        },
        headers: [
          { text: 'Date', value: 'date', key: 'date', sortable: false },
          { text: 'Source', value: 'source', key: 'source', sortable: false },
          { text: 'Amount', value: 'formattedAmount', key: 'formattedAmount', sortable: false },
          { text: 'Net Balance', value: 'net', key: 'net', sortable: false }
        ],
        moneyScheduleData: [],
      };
    },

    mounted() {
      if (this.moneyScheduleData.length === 0) {
        this.fetchMoneyScheduleData();
      }
    },
  
    computed: {
      processedData() {
        const sortedData = [...this.moneyScheduleData].sort((a, b) => {
          return new Date(a.date) - new Date(b.date);
        });
        
        let runningBalance = this.bankBalance;
        return sortedData.map(item => {
          const netBalance = runningBalance + item.amount;
          runningBalance = netBalance;
          
          return {
            ...item,
            formattedAmount: this.formatCurrency(item.amount),
            net: this.formatCurrency(netBalance),
            netValue: netBalance, 
            originalId: item.id
          };
        });
      }
    },
  
    methods: {
      formatDate(dateString) {
        if (!dateString) return '';
        
        try {
            const [year, month, day] = dateString.split('-');
            const date = new Date(parseInt(year), parseInt(month) - 1, parseInt(day));
            
            if (isNaN(date.getTime())) {
            console.error("Invalid date for formatting:", dateString);
            return '';
            }
            
            return new Intl.DateTimeFormat('en-US', {
            year: 'numeric', 
            month: '2-digit', 
            day: '2-digit'
            }).format(date);
        } catch (e) {
            console.error("Error formatting date:", e);
            return '';
        }
      },
      
      formatCurrency(value) {
        const isNegative = value < 0;
        const absValue = Math.abs(value);
        
        const formatted = new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: 'USD'
        }).format(absValue);
        
        return isNegative ? `(${formatted})` : formatted;
      },
      
      recalculateNet() {
        this.moneyScheduleData = [...this.moneyScheduleData];
      },
      
      async fetchMoneyScheduleData() {
        this.loading = true;
        try {
          const response = await ApiRequests.getMoneySchedule();
          this.moneyScheduleData = response.data.transactions;
          this.bankBalance = response.data.bank_balance;
          this.recalculateNet();
        } catch (error) {
          console.error('Error fetching money schedule data:', error);
        } finally {
          this.loading = false;
        }
      },
      
      openBalanceDialog() {
        this.editedBalance = this.bankBalance;
        this.balanceDialog = true;
      },
      
      closeBalanceDialog() {
        this.balanceDialog = false;
      },
      
      async saveBalance() {
        this.bankBalance = this.editedBalance;
        var data = {
            'source': 'Bank',
            'amount': this.editedBalance,
            'date': new Date().toISOString().split('T')[0],
        }

        try {
            console.log("Saving balance:", this.editedBalance);
            var prom = await ApiRequests.addMoneySchedule(data);
            this.moneyScheduleData = prom.data.transactions;
            this.bankBalance = prom.data.bank_balance;
        } catch (error) {
          console.error('Error updating bank balance:', error);
        }
        
        this.recalculateNet();
        
        this.closeBalanceDialog();
      },
      
      openEditDialog(item) {
        console.log("Item clicked for edit:", item);
        
        const originalIndex = this.moneyScheduleData.findIndex(i => i.id === item.originalId);
        
        if (originalIndex === -1) {
          console.error("Could not find original item in data");
          return;
        }
        
        const originalItem = this.moneyScheduleData[originalIndex];
        console.log("Original item found:", originalItem);
        
        this.editedIndex = originalIndex;
        
        this.editedItem = {
          id: originalItem.id,
          date: originalItem.date,
          source: originalItem.source,
          amount: originalItem.amount
        };
        
        console.log("Prepared editedItem:", this.editedItem);
        this.editDialog = true;
      },
      
      closeDialog() {
        this.editDialog = false;
        this.$nextTick(() => {
          this.editedItem = { ...this.defaultItem };
          this.editedIndex = -1;
        });
      },
      
      saveItem() {
        if (this.editedIndex > -1) {
          const updatedItem = {
            ...this.moneyScheduleData[this.editedIndex],
            date: this.editedItem.date,
            source: this.editedItem.source,
            amount: this.editedItem.amount
          };
          
          this.moneyScheduleData.splice(this.editedIndex, 1, updatedItem);
          
          this.updateItemInDatabase(updatedItem);
        }
        this.closeDialog();
      },
      
      openAddDialog() {
        const today = new Date().toISOString().split('T')[0];
        
        this.newItem = {
          date: today,
          source: '',
          amount: 0
        };
        
        console.log("Opening add dialog with newItem:", this.newItem);
        this.addDialog = true;
      },
      
      closeAddDialog() {
        this.addDialog = false;
      },
      
      addItem() {
        if (!this.newItem.source) {
          alert("Please enter a source");
          return;
        }
        
        const item = {
          date: this.newItem.date, 
          source: this.newItem.source,
          amount: this.newItem.amount || 0,
        };
        
        console.log("Adding new item:", item);
        
        this.addItemToDatabase(item);
        
        this.closeAddDialog();
      },
      
      async updateItemInDatabase(item) {
        try {
          console.log("Updating item:", item);
          var data = item;
          var prom = await ApiRequests.updateMoneySchedule(data);
          this.moneyScheduleData = prom.data.transactions;
          this.bankBalance = prom.data.bank_balance;
          this.recalculateNet();
        } catch (error) {
          console.error('Error updating money schedule item:', error);
        }
      },
            
      async addItemToDatabase(item) {
        try {
          console.log("Adding item to database:", item);
          var data = item;
          var prom = await ApiRequests.addMoneySchedule(data);
          this.moneyScheduleData = prom.data.transactions;
          this.bankBalance = prom.data.bank_balance;
          this.recalculateNet();
        } catch (error) {
          console.error('Error adding money schedule item:', error);
        }
      }
    },
  };
  </script>
  
  <style scoped>
  .v-data-table :deep tbody tr {
    cursor: pointer;
  }
    
  .negative-value-text {
    color: #F57F17;
    font-weight: bold;
  }
  </style>