import axios from "axios";

const API = axios.create({
    baseURL: import.meta.env.VITE_API_URL
})

class ApiRequests {
    static getCategories() {
        const url = "/categories";
        return API.get(url)
    }

    static getNewTransactions() {
        const url = "/transactions/uncategorized"
        return API.get(url)
    }

    static updateTransactionCategory(transaction) {
        const url = "/transactions"
        return API.post(url, transaction)
    }

    static addTransaction(data) {
        const url = "/transactions/add"
        return API.post(url, data)
    }

    static getSpendingPast30Categorized() {
        const url ="/spending/thismonth"
        return API.get(url)
    }

    static getSpendingLastMonthCategorized() {
        const url ="/spending/lastmonth"
        return API.get(url)
    }

    static getSpendingForSpecificMonth(month, year) {
        const url = `/spending/specific/${month}/${year}`;
        return API.get(url);
    }

    static getSpendingYearToDate() {
        const url = "/spending/yeartodate"
        return API.get(url)
    }

    static getSpendingYearToDateCategorized() {
        const url = "/spending/yeartodate/categorized"
        return API.get(url)
    }

    static getSpendingRelativeToIncome() {
        const url = "/spending/yeartodate/realtivetoincome"
        return API.get(url)
    }

    static getIncome() {
        const url = "/income";
        return API.get(url)
    }

    static addIncome(data) {
        const url = "/income";
        return API.post(url, data)
    }

    static updateIncome(data) {
        const url = "/income/update";
        return API.post(url, data)
    }

    static getRent() {
        const url = "/rent";
        return API.get(url)
    }

    static addRent(data) {
        const url = "/rent";
        return API.post(url, data)
    }

    static updateRent(data) {
        const url = "/rent/update";
        return API.post(url, data)
    }

    static getMoneyTransfers() {
        const url = "/moneytransfers";
        return API.get(url)
    }

    static addMoneyTransfer(data) {
        const url = "/moneytransfers";
        return API.post(url, data)
    }

    static updateMoneyTransfer(data) {
        const url = "/moneytransfers/update";
        return API.post(url, data);
    }

    static deleteMoneyTransfer(item_id) {
        const url = "/moneytransfers/delete/" + item_id;
        return API.post(url);
    }

    static getNetWorth() {
        const url = "/networth";
        return API.get(url)
    }

    static addNetWorth(data) {
        const url = "/networth";
        return API.post(url, data)
    }

    static getBudget() {
        const url = "/budget";
        return API.get(url)
    }

    static addBudgetItem(data) {
        const url = "/budget/add";
        return API.post(url, data)
    }

    static updateBudgetItem(data) {
        const url = "/budget/update";
        return API.patch(url, data)
    }

    static deleteBudgetItem(key) {
        const data = { key: key };
        const url = "/budget/delete";
        return API.post(url, data)
    }

    static getStockVestingSchedule(key) {
        const url = "/networth/stockvesting";
        return API.get(url)
    }

    static addStockVestingSchedule(data) {
        const url = "/networth/stockvesting";
        return API.post(url, data)
    }

    static getMoneySchedule() {
        const url = "/moneyschedule";
        return API.get(url)
    }

    static addMoneySchedule(data) {
        const url = "/moneyschedule/add";
        return API.post(url, data)
    }

    static updateMoneySchedule(data) {
        const url = "/moneyschedule/update";
        return API.post(url, data)
    }

    static forecastRetirementNeeds(data) {
        const url = "/retirement/forecast";
        return API.post(url, data)
    }

    static forecastCoastNeeds(data) {
        const url = "/retirement/coast";
        return API.post(url, data)
    }
}

export default ApiRequests;