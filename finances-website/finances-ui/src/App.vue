<template>
  <v-app>
    <v-app-bar app color="#046307" elevation="0">
      <v-app-bar-nav-icon @click.stop="drawer = !drawer"></v-app-bar-nav-icon>
      <router-link :to="{ name: 'spendingInfoView' }" style="color: white">
        <v-toolbar-title>Our Finances</v-toolbar-title>
      </router-link>
      <v-spacer></v-spacer>
    </v-app-bar>

    <v-navigation-drawer v-model="drawer" disable-resize-watcher>
      <v-list nav density="compact" color="#50C878">
        <v-list-item
          prepend-icon="mdi-invoice-arrow-right"
          title="Spending Info"
          :to="{ name: 'spendingInfoView' }"
          exact
        ></v-list-item>
        <v-list-item
          prepend-icon="mdi-relation-one-to-only-one"
          title="Categorize Transactions"
          :to="{ name: 'catTransactions' }"
        ></v-list-item>
        <v-list-item
          prepend-icon="mdi-bank-transfer"
          title="Big Money Transfers"
          :to="{ name: 'bigMoneyTransfers' }"
        ></v-list-item>
        <v-list-item
          prepend-icon="mdi-piggy-bank"
          title="Net Worth"
          :to="{ name: 'netWorth' }"
        ></v-list-item>
        <v-list-item
          prepend-icon="mdi-chart-arc"
          title="Budget"
          :to="{ name: 'budget' }"
        ></v-list-item>
      </v-list>
    </v-navigation-drawer>

    <v-main>
      <router-view />
    </v-main>
  </v-app>
</template>

<script>
import { version } from "../package.json";

export default {
  name: "App",

  data: () => ({
    drawer: true,
    v: version,
  }),
};
</script>

