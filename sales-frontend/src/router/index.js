import { createRouter, createWebHistory } from 'vue-router'
import SalesLoginView from '../views/SalesLoginView.vue'
import SalesDashboardView from '../views/SalesDashboardView.vue'
import LeadInboxView from '../views/LeadInboxView.vue'
import LeadWorkspaceView from '../views/LeadWorkspaceView.vue'
import { useSalesAuth } from '../auth.js'

const routes = [
  {
    path: '/login',
    name: 'SalesLogin',
    component: SalesLoginView
  },
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/dashboard',
    name: 'SalesDashboard',
    component: SalesDashboardView,
    meta: { requiresAuth: true }
  },
  {
    path: '/leads',
    name: 'LeadInbox',
    component: LeadInboxView,
    meta: { requiresAuth: true }
  },
  {
    path: '/leads/:id',
    name: 'LeadWorkspace',
    component: LeadWorkspaceView,
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 }
  }
})

router.beforeEach((to, from, next) => {
  const auth = useSalesAuth()
  if (to.meta.requiresAuth && !auth.isAuthenticated.value) {
    next('/login')
  } else if (to.path === '/login' && auth.isAuthenticated.value) {
    next('/dashboard')
  } else {
    next()
  }
})

export default router

