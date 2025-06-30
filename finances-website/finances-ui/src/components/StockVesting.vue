<template>
    <v-progress-linear :active="loading" :indeterminate="loading" color="#FFFFFF"/>
    <v-card justify="center" align="center">
        <v-card-title class="d-flex flex-wrap justify-space-between align-center">
                <div>
                    <h2>Stock Vesting Information</h2>
                    <h3>Vested Shares: {{ vestedShares }}, Valued at ${{ calculateValue(vestedShares) }}</h3>
                </div>
                <v-text-field
                    v-model="pricePerShare"
                    label="Current Price Per Share ($)"
                    type="number"
                    min="0"
                    step="0.01"
                    style="max-width: 200px"
                    outlined
                    dense
                    hide-details
                ></v-text-field>
        </v-card-title>
        <v-card-text>
            <v-row align="center" justify="center">
                <v-table>
                    <template v-slot:default>
                        <thead>
                            <h2>Upcoming Vesting Dates</h2>
                        </thead>
                        <tbody>
                            <tr v-for="(item, index) in upcomingVestingEvents" :key="index">
                                <td>{{ formatDate(item.date) }}</td>
                                <td class="text-right">{{ item.shares }}</td>
                                <td class="text-right">${{ calculateValue(item.shares) }}</td>
                            </tr>
                            <tr v-if="upcomingVestingEvents.length === 0">
                                <td colspan="3" class="text-center">No upcoming vesting events</td>
                            </tr>
                        </tbody>
                    </template>
                </v-table>
            </v-row>
            <v-row align="center" justify="center">
                <h2>Add New Vesting Schedule</h2>
            </v-row>
            <v-row>
                <v-col cols="12" md="2">
                    <v-text-field
                        label="Shares"
                        v-model="shares"
                        type="number"
                    />
                </v-col>
                <v-col cols="12" md="2">
                    <v-text-field
                        label="Start Date"
                        v-model="startDate"
                        type="date"
                    />
                </v-col>
                <v-col cols="12" md="2">
                    <v-text-field
                        label="End Date"
                        v-model="endDate"
                        type="date"
                    />
                </v-col>
                <v-col cols="12" md="2">
                    <v-text-field
                        label="Cliff (in months)"
                        v-model="cliff"
                        type="number"
                    />
                </v-col>
                <v-col cols="12" md="2">
                    <v-autocomplete
                        label="Vesting Frequency (in months)"
                        v-model="frequency"
                        :items="frequencyOptions"
                        outlined
                        dense
                    />
                </v-col>   
                <v-col cols="12" md="2">
                    <v-btn @click="addVestingSchedule" block rounded="lg" size="x-large" color="green">Add New Vesting</v-btn>
                </v-col>
            </v-row>
        </v-card-text>
    </v-card>
</template>

<script>
import ApiRequests from '@/api/requests';

export default {
    name: 'StockVesting',
    data() {
        return {
            cliff: 12,
            endDate: null,
            frequency: 'Quarterly',
            frequencyOptions: ['Monthly', 'Quarterly', 'Semi-Annually', 'Annually'],
            loading: true,
            pricePerShare: 7,
            shares: null,
            startDate: null,
            vestingData: [],
            vestedShares: 0,
        };
    },
    computed: {
        upcomingVestingEvents() {
            const today = new Date();
            today.setHours(0, 0, 0, 0);
            
            const vestingArray = Object.entries(this.vestingData).map(([date, shares]) => ({
                date,
                shares
            }));
            
            return vestingArray
                .filter(item => {
                    const vestingDate = new Date(item.date);
                    return vestingDate >= today;
                })
                .sort((a, b) => new Date(a.date) - new Date(b.date))
                .slice(0, 3);
        }
    },

    watch: {
    },

    mounted() {
        this.fetchVestingData();
    },

    methods: {
        async fetchVestingData() {
                    try {
                        const response = await ApiRequests.getStockVestingSchedule();
                        this.vestingData = response.data.vesting_schedule;
                        this.vestedShares = response.data.total_vested_shares;
                    } catch (error) {
                        console.error('Error fetching stock vesting data:', error);
                    } finally {
                        this.loading = false;
                    }
                },

                async addVestingSchedule() {
            if (!this.shares || !this.startDate || !this.endDate) {
                alert('Please fill in all fields.');
                return;
            }

            // Format dates to YYYY-MM-DD if they're not already in that format
            const formatDate = (dateString) => {
                if (!dateString) return null;
                
                // If already in YYYY-MM-DD format, return as is
                if (/^\d{4}-\d{2}-\d{2}$/.test(dateString)) {
                    return dateString;
                }
                
                // If in MM/DD/YYYY format, convert to YYYY-MM-DD
                const parts = dateString.split('/');
                if (parts.length === 3) {
                    // Rearrange MM/DD/YYYY to YYYY-MM-DD
                    return `${parts[2]}-${parts[0].padStart(2, '0')}-${parts[1].padStart(2, '0')}`;
                }
                
                // Otherwise, just return the original string
                return dateString;
            };

            const vestingSchedule = {
                shares: this.shares,
                start: formatDate(this.startDate),
                end: formatDate(this.endDate),
                cliff: this.cliff,
                schedule: this.frequency.toLowerCase()
            };

            try {
                const response = await ApiRequests.addStockVestingSchedule(vestingSchedule);
                console.log('API Response:', response);
                
                if (response.data && response.data.error) {
                    alert('Error: ' + response.data.error);
                } else {
                    alert('Vesting schedule added successfully!');
                    this.fetchVestingData();
                }
            } catch (error) {
                console.error('Error adding vesting schedule:', error);
                alert('Error: ' + (error.response?.data?.error || error.message || 'Unknown error'));
            }
        },

        formatDate(dateString) {
            try {
                // Split the YYYY-MM-DD string and create a date object with explicit components
                // This avoids timezone issues
                const [year, month, day] = dateString.split('-');
                
                // Create date using local timezone (months are 0-indexed in JS)
                const date = new Date(parseInt(year), parseInt(month) - 1, parseInt(day));
                
                const options = { year: 'numeric', month: 'short', day: 'numeric' };
                return date.toLocaleDateString(undefined, options);
            } catch (e) {
                console.error("Error formatting date:", e);
                return dateString; // Fallback to original string
            }
        },

        calculateValue(shares) {
            return (shares * this.pricePerShare).toLocaleString(undefined, {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            });
        }
    },
};
</script>