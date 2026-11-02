<template>
  <div class="min-h-screen bg-surface-canvas flex flex-col">
    <SalesNavbar />

    <main class="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      <!-- Welcome Header -->
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 class="text-2xl sm:text-3xl font-extrabold tracking-tight text-brand-deep">
            Sales & Underwriting Overview
          </h1>
          <p class="text-xs sm:text-sm text-brand-muted mt-1 font-medium">
            Active loan pipeline performance, stage distributions, and high-priority underwriting actions.
          </p>
        </div>

        <router-link
          to="/leads"
          class="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-brand text-white text-xs sm:text-sm font-bold shadow-sm hover:bg-brand-hover transition self-start sm:self-auto"
        >
          <Inbox class="w-4 h-4" />
          <span>Open Leads Inbox</span>
        </router-link>
      </div>

      <!-- Loading State -->
      <div v-if="isLoading" class="py-16 text-center space-y-3">
        <Loader2 class="w-8 h-8 animate-spin text-brand mx-auto" />
        <p class="text-xs sm:text-sm font-semibold text-brand-muted">Loading pipeline metrics...</p>
      </div>

      <!-- Dashboard Grid -->
      <div v-else class="space-y-8">
        <!-- 4-Card Top Metrics -->
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <!-- Metric 1: Total Leads -->
          <div class="p-5 rounded-2xl bg-white border border-surface-border shadow-2xs space-y-2">
            <div class="flex items-center justify-between text-brand-muted">
              <span class="text-xs font-bold uppercase tracking-wider">Total Scoped Leads</span>
              <Users class="w-4 h-4 text-brand" />
            </div>
            <p class="text-2xl sm:text-3xl font-extrabold text-brand-deep font-tabular">
              {{ metrics.total_leads }}
            </p>
            <span class="text-[11px] text-brand-muted font-medium">Within your authorized scope</span>
          </div>

          <!-- Metric 2: Pipeline Volume -->
          <div class="p-5 rounded-2xl bg-white border border-surface-border shadow-2xs space-y-2">
            <div class="flex items-center justify-between text-brand-muted">
              <span class="text-xs font-bold uppercase tracking-wider">Pipeline Loan Value</span>
              <IndianRupee class="w-4 h-4 text-sage" />
            </div>
            <p class="text-2xl sm:text-3xl font-extrabold text-brand-deep font-tabular">
              ₹{{ formatVolume(metrics.pipeline_volume) }}
            </p>
            <span class="text-[11px] text-brand-muted font-medium">Cumulative requested loan quantum</span>
          </div>

          <!-- Metric 3: Conversion Rate -->
          <div class="p-5 rounded-2xl bg-white border border-surface-border shadow-2xs space-y-2">
            <div class="flex items-center justify-between text-brand-muted">
              <span class="text-xs font-bold uppercase tracking-wider">Qualification Rate</span>
              <TrendingUp class="w-4 h-4 text-brand" />
            </div>
            <p class="text-2xl sm:text-3xl font-extrabold text-brand-deep font-tabular">
              {{ metrics.conversion_rate_pct }}%
            </p>
            <span class="text-[11px] text-brand-muted font-medium">Qualified / Total Leads</span>
          </div>

          <!-- Metric 4: Tasks Due -->
          <div class="p-5 rounded-2xl bg-white border border-surface-border shadow-2xs space-y-2">
            <div class="flex items-center justify-between text-brand-muted">
              <span class="text-xs font-bold uppercase tracking-wider">Follow-Up Tasks</span>
              <Clock class="w-4 h-4 text-amber-600" />
            </div>
            <div class="flex items-baseline gap-2">
              <p class="text-2xl sm:text-3xl font-extrabold text-brand-deep font-tabular">
                {{ metrics.pending_tasks }}
              </p>
              <span v-if="metrics.overdue_tasks > 0" class="text-xs font-bold text-red-600">
                ({{ metrics.overdue_tasks }} overdue)
              </span>
            </div>
            <span class="text-[11px] text-brand-muted font-medium">Callbacks and document pickups</span>
          </div>
        </div>

        <!-- Pipeline Status Breakdown -->
        <div class="p-6 rounded-3xl bg-white border border-surface-border shadow-2xs space-y-5">
          <div class="flex items-center justify-between">
            <div>
              <h3 class="text-base sm:text-lg font-bold text-brand-deep">
                Pipeline Lifecycle Distribution
              </h3>
              <p class="text-xs text-brand-muted">Click a status to jump directly to filtered leads in the inbox.</p>
            </div>
          </div>

          <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            <router-link
              v-for="(count, st) in statusBreakdown"
              :key="st"
              :to="`/leads?status=${st}`"
              class="p-4 rounded-2xl border border-surface-border hover:border-brand/40 bg-surface-canvas hover:bg-white transition text-center space-y-1 block cursor-pointer group"
            >
              <span class="text-[10px] uppercase font-bold tracking-wider text-brand-muted block truncate group-hover:text-brand">
                {{ formatStatus(st) }}
              </span>
              <p class="text-xl font-extrabold text-brand-deep font-tabular">
                {{ count }}
              </p>
            </router-link>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { 
  Inbox, 
  Users, 
  IndianRupee, 
  TrendingUp, 
  Clock, 
  Loader2 
} from 'lucide-vue-next'
import SalesNavbar from '../components/SalesNavbar.vue'

const metrics = ref({
  total_leads: 0,
  pipeline_volume: 0,
  conversion_rate_pct: 0,
  pending_tasks: 0,
  overdue_tasks: 0
})
const statusBreakdown = ref({})
const isLoading = ref(true)

const fetchDashboard = async () => {
  isLoading.value = true
  try {
    const token = localStorage.getItem('credence_sales_token')
    const res = await fetch('/api/sales/dashboard', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    if (res.ok) {
      const data = await res.json()
      metrics.value = data.metrics || metrics.value
      statusBreakdown.value = data.status_breakdown || {}
    }
  } catch (err) {
    console.error('Failed to load sales dashboard:', err)
  } finally {
    isLoading.value = false
  }
}

const formatVolume = (val) => {
  if (!val) return '0'
  if (val >= 10000000) {
    return `${(val / 10000000).toFixed(2)} Cr`
  }
  if (val >= 100000) {
    return `${(val / 100000).toFixed(1)} L`
  }
  return Number(val).toLocaleString('en-IN')
}

const formatStatus = (s) => {
  const map = {
    'NEW': 'New',
    'ASSIGNED': 'Assigned',
    'CONTACT_ATTEMPTED': 'Attempted',
    'CONTACTED': 'Contacted',
    'QUALIFIED': 'Qualified',
    'NOT_QUALIFIED': 'Ineligible',
    'CLOSED_LOST': 'Closed'
  }
  return map[s] || s
}

onMounted(() => {
  fetchDashboard()
})
</script>

