import { createRouter, createWebHistory } from 'vue-router'

import AppLayout from '@/layouts/AppLayout.vue'
import AlertsView from '@/views/AlertsView.vue'
import ConceptView from '@/views/ConceptView.vue'
import CorrelationView from '@/views/CorrelationView.vue'
import DashboardView from '@/views/DashboardView.vue'
import DataAdminView from '@/views/DataAdminView.vue'
import DisciplineView from '@/views/DisciplineView.vue'
import StockLinkageView from '@/views/StockLinkageView.vue'
import WatchlistView from '@/views/WatchlistView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      component: AppLayout,
      redirect: '/dashboard',
      children: [
        { path: 'dashboard', name: 'dashboard', component: DashboardView, meta: { title: '总览' } },
        { path: 'discipline', name: 'discipline', component: DisciplineView, meta: { title: '交易纪律' } },
        { path: 'stock-linkage', name: 'stock-linkage', component: StockLinkageView, meta: { title: '股票关联' } },
        { path: 'concept', name: 'concept', component: ConceptView, meta: { title: '概念专题' } },
        { path: 'correlation', name: 'correlation', component: CorrelationView, meta: { title: '相关性分析' } },
        { path: 'alerts', name: 'alerts', component: AlertsView, meta: { title: '事件提醒' } },
        { path: 'watchlist', name: 'watchlist', component: WatchlistView, meta: { title: '自选观察' } },
        { path: 'data-admin', name: 'data-admin', component: DataAdminView, meta: { title: '数据管理' } }
      ]
    }
  ]
})

router.afterEach((to) => {
  const pageTitle = typeof to.meta.title === 'string' ? to.meta.title : 'Stock Research Workspace'
  document.title = `${pageTitle} | Stock Research Workspace`
})

export default router
