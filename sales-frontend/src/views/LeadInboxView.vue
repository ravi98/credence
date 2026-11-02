<template>
  <div class="min-h-screen bg-surface-canvas flex flex-col">
    <SalesNavbar />

    <main class="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      <!-- Title & Search Bar -->
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 class="text-2xl font-extrabold tracking-tight text-brand-deep">
            Leads Inbox
          </h1>
          <p class="text-xs sm:text-sm text-brand-muted mt-0.5">
            Manage incoming applications, review borrower criteria, and advance stage lifecycles.
          </p>
        </div>

        <!-- Search Input -->
        <div class="relative w-full sm:w-72">
          <Search class="w-4 h-4 text-brand-muted absolute left-3.5 top-3" />
          <input 
            v-model="searchQuery"
            @input="debounceSearch"
            type="text" 
            placeholder="Search reference, borrower..."
            class="w-full text-xs sm:text-sm pl-9 pr-3.5 py-2.5 rounded-xl border border-surface-border bg-white outline-none focus:border-brand"
          />
        </div>
      </div>

      <!-- Status Filter Tabs -->
      <div class="flex items-center gap-2 overflow-x-auto pb-1 text-xs font-bold scrollbar-none">
        <button
          v-for="tab in statusTabs"
          :key="tab.value"
          @click="selectStatus(tab.value)"
          class="px-3.5 py-2 rounded-xl transition whitespace-nowrap cursor-pointer border"
          :class="activeStatus === tab.value ? 'bg-brand text-white border-brand shadow-2xs' : 'bg-white text-brand-deep border-surface-border hover:bg-surface-secondary'"
        >
          {{ tab.label }}
        </button>
      </div>

      <!-- Loading State -->
      <div v-if="isLoading" class="py-16 text-center space-y-3">
        <Loader2 class="w-8 h-8 animate-spin text-brand mx-auto" />
        <p class="text-xs sm:text-sm font-semibold text-brand-muted">Fetching leads...</p>
      </div>

      <!-- Empty State -->
      <div v-else-if="leads.length === 0" class="p-12 rounded-3xl bg-white border border-surface-border text-center space-y-3">
        <Inbox class="w-10 h-10 text-brand-muted mx-auto" />
        <h3 class="text-base font-bold text-brand-deep">No Leads Found</h3>
        <p class="text-xs text-brand-muted max-w-sm mx-auto">
          No loan applications match your current status filter or search parameters.
        </p>
      </div>

      <!-- Leads Table -->
      <div v-else class="bg-white rounded-3xl border border-surface-border shadow-2xs overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full text-left border-collapse text-xs sm:text-sm">
            <thead>
              <tr class="border-b border-surface-border bg-surface-canvas/60 text-[11px] uppercase tracking-wider font-extrabold text-brand-muted">
                <th class="py-3.5 px-4 sm:px-6">Reference & Date</th>
                <th class="py-3.5 px-4">Applicant</th>
                <th class="py-3.5 px-4">Product & Bank</th>
                <th class="py-3.5 px-4">Quantum</th>
                <th class="py-3.5 px-4">Assigned To</th>
                <th class="py-3.5 px-4">Status</th>
                <th class="py-3.5 px-4 sm:px-6 text-right">Action</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-surface-border">
              <tr 
                v-for="lead in leads" 
                :key="lead.id"
                class="hover:bg-surface-secondary/40 transition group cursor-pointer"
                @click="openLead(lead.id)"
              >
                <!-- Reference & Date -->
                <td class="py-4 px-4 sm:px-6">
                  <span class="font-mono font-bold text-brand block">{{ lead.enquiry_reference }}</span>
                  <span class="text-[11px] text-brand-muted font-medium">{{ formatDate(lead.created_at) }}</span>
                </td>

                <!-- Applicant -->
                <td class="py-4 px-4">
                  <span class="font-bold text-brand-deep block">{{ lead.customer_name }}</span>
                  <span class="text-[11px] text-brand-muted">{{ lead.customer_city || 'India' }}</span>
                </td>

                <!-- Product -->
                <td class="py-4 px-4">
                  <span class="font-bold text-brand-deep block max-w-xs truncate">
                    {{ lead.primary_product?.scheme_name || lead.loan_category }}
                  </span>
                  <span class="text-[11px] text-brand font-semibold">
                    {{ lead.primary_product?.institution }} · {{ lead.primary_product?.interest_rate }}
                  </span>
                </td>

                <!-- Quantum -->
                <td class="py-4 px-4 font-tabular">
                  <span class="font-bold text-brand-deep block">₹{{ formatCurrency(lead.requested_amount) }}</span>
                  <span class="text-[11px] text-brand-muted">{{ Math.round((lead.preferred_tenure_months || 240) / 12) }} Yrs</span>
                </td>

                <!-- Assigned Officer -->
                <td class="py-4 px-4">
                  <span v-if="lead.assigned_to" class="font-medium text-brand-deep block">
                    {{ lead.assigned_to.name }}
                  </span>
                  <span v-else class="text-xs text-amber-700 bg-amber-50 px-2 py-0.5 rounded font-bold border border-amber-200">
                    Unassigned
                  </span>
                </td>

                <!-- Status Badge -->
                <td class="py-4 px-4">
                  <LeadStatusBadge :status="lead.current_status" />
                </td>

                <!-- Actions -->
                <td class="py-4 px-4 sm:px-6 text-right space-x-2" @click.stop>
                  <button 
                    v-if="auth.isManager.value"
                    @click="openAssign(lead)"
                    class="px-2.5 py-1 rounded-lg border border-surface-border text-xs font-semibold hover:border-brand hover:text-brand transition cursor-pointer"
                  >
                    Assign
                  </button>
                  <router-link
                    :to="`/leads/${lead.id}`"
                    class="px-3 py-1 rounded-lg bg-brand text-white text-xs font-bold hover:bg-brand-hover transition inline-block"
                  >
                    Open
                  </router-link>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </main>

    <!-- Assignment Modal -->
    <AssignmentModal
      :is-open="assignModalOpen"
      :lead-id="selectedLeadForAssign?.id"
      :lead-reference="selectedLeadForAssign?.enquiry_reference"
      @close="assignModalOpen = false"
      @assigned="handleAssigned"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Search, Inbox, Loader2 } from 'lucide-vue-next'
import SalesNavbar from '../components/SalesNavbar.vue'
import LeadStatusBadge from '../components/LeadStatusBadge.vue'
import AssignmentModal from '../components/AssignmentModal.vue'
import { useSalesAuth } from '../auth.js'

const router = useRouter()
const route = useRoute()
const auth = useSalesAuth()

const leads = ref([])
const isLoading = ref(true)
const searchQuery = ref('')
const activeStatus = ref(route.query.status || 'ALL')

const assignModalOpen = ref(false)
const selectedLeadForAssign = ref(null)

let searchTimeout = null

const statusTabs = [
  { label: 'All Leads', value: 'ALL' },
  { label: 'New', value: 'NEW' },
  { label: 'Assigned', value: 'ASSIGNED' },
  { label: 'Contact Attempted', value: 'CONTACT_ATTEMPTED' },
  { label: 'Contacted', value: 'CONTACTED' },
  { label: 'Qualified', value: 'QUALIFIED' },
  { label: 'Ineligible / Lost', value: 'CLOSED_LOST' }
]

const fetchLeads = async () => {
  isLoading.value = true
  try {
    const token = localStorage.getItem('credence_sales_token')
    let url = `/api/sales/leads?limit=50`
    if (activeStatus.value && activeStatus.value !== 'ALL') {
      url += `&status=${activeStatus.value}`
    }
    if (searchQuery.value.trim()) {
      url += `&search=${encodeURIComponent(searchQuery.value.trim())}`
    }

    const res = await fetch(url, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    if (res.ok) {
      const data = await res.json()
      leads.value = data.leads || []
    }
  } catch (err) {
    console.error('Failed to load leads:', err)
  } finally {
    isLoading.value = false
  }
}

const selectStatus = (val) => {
  activeStatus.value = val
  router.replace({ query: { ...route.query, status: val !== 'ALL' ? val : undefined } })
  fetchLeads()
}

const debounceSearch = () => {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    fetchLeads()
  }, 300)
}

const openLead = (id) => {
  router.push(`/leads/${id}`)
}

const openAssign = (lead) => {
  selectedLeadForAssign.value = lead
  assignModalOpen.value = true
}

const handleAssigned = () => {
  fetchLeads()
}

const formatCurrency = (val) => {
  if (!val) return '0'
  return Number(val).toLocaleString('en-IN')
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  try {
    const d = new Date(dateStr)
    return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
  } catch (e) {
    return dateStr
  }
}

onMounted(() => {
  fetchLeads()
})
</script>

