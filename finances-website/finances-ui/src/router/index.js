import { createRouter, createWebHistory } from 'vue-router'
import SpendingInfoView from "@/pages/SpendingInfoView.vue"
import CatTransactions from '@/pages/CatTransactions.vue'
import BigMoneyTransfers from '@/pages/BigMoneyTransfers.vue'
import NetWorth from '@/pages/NetWorth.vue'
import Budget from '@/pages/Budget.vue'

const routes =[
    {
        path: "/",
        name: "spendingInfoView",
        component: SpendingInfoView
    },
    {
        path: "/catTransactions",
        name: "catTransactions",
        component: CatTransactions
    },
    {
        path: "/bigMoneyTransfers",
        name: "bigMoneyTransfers",
        component: BigMoneyTransfers
    },
    {
        path: "/netWorth",
        name: "netWorth",
        component: NetWorth
    },
    {
        path: "/budget",
        name: "budget",
        component: Budget
    },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

// Workaround for https://github.com/vitejs/vite/issues/11804
router.onError((err, to) => {
  if (err?.message?.includes?.('Failed to fetch dynamically imported module')) {
    if (!localStorage.getItem('vuetify:dynamic-reload')) {
      console.log('Reloading page to fix dynamic import error')
      localStorage.setItem('vuetify:dynamic-reload', 'true')
      location.assign(to.fullPath)
    } else {
      console.error('Dynamic import error, reloading page did not fix it', err)
    }
  } else {
    console.error(err)
  }
})

router.isReady().then(() => {
  localStorage.removeItem('vuetify:dynamic-reload')
})

export default router
