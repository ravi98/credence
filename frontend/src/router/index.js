import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import AdvisorView from '../views/AdvisorView.vue'
import ExploreView from '../views/ExploreView.vue'
import CompareView from '../views/CompareView.vue'
import LearnView from '../views/LearnView.vue'
import EmiCalculatorView from '../views/EmiCalculatorView.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: HomeView
  },
  {
    path: '/advisor',
    name: 'Advisor',
    component: AdvisorView
  },
  {
    path: '/explore',
    name: 'Explore',
    component: ExploreView
  },
  {
    path: '/compare',
    name: 'Compare',
    component: CompareView
  },
  {
    path: '/learn',
    name: 'Learn',
    component: LearnView
  },
  {
    path: '/calculators',
    redirect: '/calculators/emi'
  },
  {
    path: '/calculators/emi',
    name: 'EmiCalculator',
    component: EmiCalculatorView
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 }
  }
})

export default router

