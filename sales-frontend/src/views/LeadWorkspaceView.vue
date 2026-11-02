<template>
  <div class="min-h-screen bg-surface-canvas flex flex-col">
    <SalesNavbar />

    <!-- Loading State -->
    <div v-if="isLoading" class="py-24 text-center space-y-3">
      <Loader2 class="w-8 h-8 animate-spin text-brand mx-auto" />
      <p class="text-xs sm:text-sm font-semibold text-brand-muted">Opening lead workspace...</p>
    </div>

    <!-- Workspace Main Container -->
    <main v-else-if="lead" class="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
      <!-- Breadcrumb & Top Bar -->
      <div class="flex items-center justify-between text-xs font-semibold text-brand-muted">
        <router-link to="/leads" class="hover:text-brand flex items-center gap-1">
          <ArrowLeft class="w-3.5 h-3.5" />
          <span>Back to Leads Inbox</span>
        </router-link>
        <span class="font-mono">Submitted {{ formatDate(lead.created_at) }}</span>
      </div>

      <!-- Lead Summary Header Card -->
      <div class="p-6 rounded-3xl bg-white border border-surface-border shadow-2xs space-y-4">
        <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <!-- Left: Name & Reference -->
          <div class="space-y-1">
            <div class="flex items-center gap-3 flex-wrap">
              <h1 class="text-2xl font-extrabold tracking-tight text-brand-deep">
                {{ lead.borrower_profile_snapshot?.full_name || 'Borrower' }}
              </h1>
              <span class="font-mono text-sm font-bold text-brand bg-surface-secondary px-2.5 py-0.5 rounded-lg border border-surface-border">
                {{ lead.enquiry_reference }}
              </span>
              <LeadStatusBadge :status="lead.current_status" />
            </div>

            <!-- Contact & Profile Details Subline -->
            <div class="flex items-center gap-4 text-xs text-brand-muted font-medium flex-wrap pt-1">
              <span v-if="lead.contact_details_snapshot?.phone" class="flex items-center gap-1 text-brand-deep font-semibold">
                <Phone class="w-3.5 h-3.5 text-brand" />
                {{ lead.contact_details_snapshot.phone }}
              </span>
              <span v-if="lead.contact_details_snapshot?.email" class="flex items-center gap-1">
                <Mail class="w-3.5 h-3.5 text-brand" />
                {{ lead.contact_details_snapshot.email }}
              </span>
              <span v-if="lead.borrower_profile_snapshot?.city" class="flex items-center gap-1">
                <MapPin class="w-3.5 h-3.5 text-brand" />
                {{ lead.borrower_profile_snapshot.city }}
              </span>
              <span class="text-brand font-bold">
                {{ lead.loan_category }} · ₹{{ formatCurrency(lead.requested_amount) }}
              </span>
            </div>
          </div>

          <!-- Right: Status Transition Controls & Assign Action -->
          <div class="flex items-center gap-3 flex-wrap self-start lg:self-auto">
            <!-- Status Transition Dropdown -->
            <div class="flex items-center gap-2">
              <label class="text-xs font-bold text-brand-muted">Stage:</label>
              <select 
                v-model="selectedNewStatus"
                @change="handleStatusChange"
                :disabled="isUpdatingStatus"
                class="text-xs font-bold px-3 py-2 rounded-xl border border-surface-border bg-surface-secondary hover:border-brand outline-none cursor-pointer"
              >
                <option value="NEW">New Lead</option>
                <option value="ASSIGNED">Assigned</option>
                <option value="CONTACT_ATTEMPTED">Contact Attempted</option>
                <option value="CONTACTED">Contacted</option>
                <option value="QUALIFIED">Qualified</option>
                <option value="NOT_QUALIFIED">Ineligible</option>
                <option value="CLOSED_LOST">Closed / Lost</option>
              </select>
            </div>

            <!-- Reassign Button if Manager -->
            <button
              v-if="auth.isManager.value"
              @click="assignModalOpen = true"
              class="px-3.5 py-2 rounded-xl bg-surface-secondary border border-surface-border text-xs font-bold text-brand-deep hover:border-brand hover:text-brand transition cursor-pointer"
            >
              {{ lead.assigned_to ? `Reassign (${lead.assigned_to.name})` : 'Assign Lead' }}
            </button>
          </div>
        </div>
      </div>

      <!-- Navigation Tabs -->
      <div class="flex items-center gap-2 border-b border-surface-border overflow-x-auto text-xs font-bold">
        <button
          v-for="t in tabs"
          :key="t.id"
          @click="activeTab = t.id"
          class="px-4 py-3 border-b-2 transition flex items-center gap-2 whitespace-nowrap cursor-pointer"
          :class="activeTab === t.id ? 'border-brand text-brand' : 'border-transparent text-brand-muted hover:text-brand-deep'"
        >
          <span>{{ t.label }}</span>
          <span 
            v-if="t.badge" 
            class="px-1.5 py-0.2 rounded-full text-[10px]"
            :class="activeTab === t.id ? 'bg-brand/10 text-brand' : 'bg-surface-secondary text-brand-muted'"
          >
            {{ t.badge }}
          </span>
        </button>
      </div>

      <!-- ==================== TAB 1: AI UNDERWRITING BRIEFING ==================== -->
      <div v-if="activeTab === 'AI_BRIEFING'" class="space-y-4">
        <AIHandoffCard 
          v-if="lead.ai_handoff_summary"
          :summary="lead.ai_handoff_summary"
        />
        <div v-else class="p-8 rounded-3xl bg-white border border-surface-border text-center space-y-2">
          <Loader2 class="w-6 h-6 animate-spin text-brand mx-auto" />
          <p class="text-xs font-semibold text-brand-muted">AI Underwriting Handoff Briefing is generating...</p>
        </div>
      </div>

      <!-- ==================== TAB 2: BORROWER SNAPSHOT & PRODUCTS ==================== -->
      <div v-if="activeTab === 'SNAPSHOT'" class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Borrower Snapshot (2 Cols) -->
        <div class="lg:col-span-2 space-y-6">
          <div class="p-6 rounded-3xl bg-white border border-surface-border shadow-2xs space-y-4">
            <h3 class="text-xs font-bold uppercase tracking-wider text-brand-deep">
              Immutable Borrower Profile Snapshot
            </h3>
            <div class="grid grid-cols-2 sm:grid-cols-3 gap-4 text-xs">
              <div>
                <span class="text-brand-muted block">Monthly Net Income:</span>
                <strong class="font-bold text-brand-deep text-sm font-tabular">₹{{ formatCurrency(lead.borrower_profile_snapshot?.monthly_income) }}</strong>
              </div>
              <div>
                <span class="text-brand-muted block">Requested Quantum:</span>
                <strong class="font-bold text-brand-deep text-sm font-tabular">₹{{ formatCurrency(lead.requested_amount) }}</strong>
              </div>
              <div>
                <span class="text-brand-muted block">Preferred Tenure:</span>
                <strong class="font-bold text-brand-deep text-sm">{{ Math.round((lead.preferred_tenure_months || 240) / 12) }} Years ({{ lead.preferred_tenure_months }} mo)</strong>
              </div>
              <div>
                <span class="text-brand-muted block">Employment Type:</span>
                <strong class="font-bold text-brand-deep text-sm">{{ lead.borrower_profile_snapshot?.employment }}</strong>
              </div>
              <div>
                <span class="text-brand-muted block">Employer / Company:</span>
                <strong class="font-bold text-brand-deep text-sm">{{ lead.borrower_profile_snapshot?.company_name || 'Not Specified' }}</strong>
              </div>
              <div>
                <span class="text-brand-muted block">Self-Reported CIBIL:</span>
                <strong class="font-bold text-brand-deep text-sm">{{ lead.borrower_profile_snapshot?.cibil_score || 750 }}</strong>
              </div>
              <div>
                <span class="text-brand-muted block">Existing Monthly EMIs:</span>
                <strong class="font-bold text-brand-deep text-sm font-tabular">₹{{ formatCurrency(lead.borrower_profile_snapshot?.existing_emi || 0) }}</strong>
              </div>
              <div>
                <span class="text-brand-muted block">Borrower City:</span>
                <strong class="font-bold text-brand-deep text-sm">{{ lead.borrower_profile_snapshot?.city }}</strong>
              </div>
            </div>
          </div>

          <!-- Evaluated Products -->
          <div class="p-6 rounded-3xl bg-white border border-surface-border shadow-2xs space-y-4">
            <h3 class="text-xs font-bold uppercase tracking-wider text-brand-deep">
              Catalog Products Evaluated in Chat
            </h3>
            <div class="space-y-3">
              <div 
                v-for="p in lead.products" 
                :key="p.id"
                class="p-4 rounded-2xl border border-surface-border flex items-start justify-between gap-3"
              >
                <div>
                  <span class="text-[10px] font-extrabold uppercase px-2 py-0.5 rounded-md" :class="p.preference_type === 'PRIMARY' ? 'bg-brand/10 text-brand' : 'bg-surface-secondary text-brand-muted'">
                    {{ p.preference_type }} SELECTION
                  </span>
                  <h4 class="font-bold text-brand-deep text-base mt-1">{{ p.scheme_name }}</h4>
                  <p class="text-xs text-brand font-semibold">{{ p.institution }} · {{ p.product_snapshot?.interest_rate_range || 'Market Rate' }}</p>
                  <p class="text-[11px] text-brand-muted mt-1">Benchmark: {{ p.product_snapshot?.benchmark || 'EBLR' }} · Max Tenure: {{ p.product_snapshot?.max_tenure_years }} Yrs</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Contact Preferences (1 Col) -->
        <div class="space-y-6">
          <div class="p-6 rounded-3xl bg-white border border-surface-border shadow-2xs space-y-4">
            <h3 class="text-xs font-bold uppercase tracking-wider text-brand-deep">
              Customer Contact Preferences
            </h3>
            <div class="space-y-3 text-xs">
              <div>
                <span class="text-brand-muted block">Preferred Channel:</span>
                <strong class="font-bold text-brand-deep text-sm">{{ lead.contact_preferences?.preferred_channel || 'WhatsApp' }}</strong>
              </div>
              <div>
                <span class="text-brand-muted block">Preferred Time Window:</span>
                <strong class="font-bold text-brand-deep text-sm">{{ lead.contact_preferences?.preferred_time_slot || 'Morning (10 AM - 1 PM)' }}</strong>
              </div>
              <div v-if="lead.contact_preferences?.notes">
                <span class="text-brand-muted block">Borrower Special Notes:</span>
                <p class="p-2.5 rounded-xl bg-surface-secondary text-brand-deep font-medium mt-1">
                  {{ lead.contact_preferences.notes }}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ==================== TAB 3: NOTES & TIMELINE ==================== -->
      <div v-if="activeTab === 'NOTES'" class="max-w-3xl space-y-4">
        <NotesTimeline 
          :lead-id="lead.id" 
          :notes="lead.notes" 
          @note-added="refreshLead"
        />
      </div>

      <!-- ==================== TAB 4: TASKS ==================== -->
      <div v-if="activeTab === 'TASKS'" class="max-w-3xl space-y-4">
        <TasksManager 
          :lead-id="lead.id" 
          :tasks="lead.tasks" 
          @task-updated="refreshLead"
        />
      </div>

      <!-- ==================== TAB 5: BANK APPLICATIONS ==================== -->
      <div v-if="activeTab === 'APPLICATIONS'" class="space-y-4">
        <!-- New Application Form -->
        <div class="p-5 rounded-2xl bg-white border border-surface-border space-y-3 max-w-2xl">
          <h4 class="text-xs font-bold uppercase tracking-wider text-brand-deep">Log Official Bank Application</h4>
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <input 
              v-model="newApp.lenderName" 
              placeholder="Bank Name (e.g. SBI)" 
              class="text-xs px-3 py-2 rounded-xl border border-surface-border" 
            />
            <input 
              v-model="newApp.productRef" 
              placeholder="Scheme Ref / Slug" 
              class="text-xs px-3 py-2 rounded-xl border border-surface-border" 
            />
            <input 
              v-model="newApp.appRef" 
              placeholder="Bank App / Ref No." 
              class="text-xs px-3 py-2 rounded-xl border border-surface-border" 
            />
          </div>
          <div class="flex justify-end">
            <button 
              @click="submitBankApp"
              :disabled="!newApp.lenderName.trim()"
              class="px-4 py-2 rounded-xl bg-brand text-white text-xs font-bold hover:bg-brand-hover disabled:opacity-50 transition cursor-pointer"
            >
              Record Application
            </button>
          </div>
        </div>

        <!-- Applications List -->
        <div v-if="lead.applications?.length === 0" class="p-8 rounded-3xl bg-white border border-surface-border text-center text-xs text-brand-muted">
          No external lender applications logged yet.
        </div>
        <div v-else class="space-y-3">
          <div 
            v-for="app in lead.applications" 
            :key="app.id"
            class="p-4 rounded-2xl bg-white border border-surface-border flex items-center justify-between gap-3"
          >
            <div>
              <h4 class="font-bold text-brand-deep text-sm">{{ app.lender_name }}</h4>
              <p class="text-xs text-brand-muted font-medium">Ref: {{ app.application_reference || 'Pending Allocation' }}</p>
            </div>
            <span class="px-2.5 py-1 rounded-full text-xs font-bold bg-sage/10 text-sage border border-sage/20">
              {{ app.current_status }}
            </span>
          </div>
        </div>
      </div>

      <!-- ==================== TAB 6: AUDIT TRAIL ==================== -->
      <div v-if="activeTab === 'AUDIT'" class="max-w-3xl space-y-3">
        <div class="p-6 rounded-3xl bg-white border border-surface-border shadow-2xs space-y-3">
          <h3 class="text-xs font-bold uppercase tracking-wider text-brand-deep">Application Lifecycle Audit Log</h3>
          <div class="space-y-2">
            <div 
              v-for="h in lead.status_history" 
              :key="h.id"
              class="p-3 rounded-xl bg-surface-canvas border border-surface-border flex items-center justify-between text-xs"
            >
              <div>
                <strong class="font-bold text-brand-deep">{{ h.new_status }}</strong>
                <span class="text-brand-muted ml-1">— {{ h.reason }} (by {{ h.changed_by }})</span>
              </div>
              <span class="text-brand-muted text-[11px] font-mono">{{ formatDate(h.created_at) }}</span>
            </div>
          </div>
        </div>
      </div>
    </main>

    <!-- Assignment Modal -->
    <AssignmentModal
      :is-open="assignModalOpen"
      :lead-id="lead?.id"
      :lead-reference="lead?.enquiry_reference"
      @close="assignModalOpen = false"
      @assigned="refreshLead"
    />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { 
  ArrowLeft, 
  Phone, 
  Mail, 
  MapPin, 
  Loader2 
} from 'lucide-vue-next'
import SalesNavbar from '../components/SalesNavbar.vue'
import LeadStatusBadge from '../components/LeadStatusBadge.vue'
import AIHandoffCard from '../components/AIHandoffCard.vue'
import NotesTimeline from '../components/NotesTimeline.vue'
import TasksManager from '../components/TasksManager.vue'
import AssignmentModal from '../components/AssignmentModal.vue'
import { useSalesAuth } from '../auth.js'

const route = useRoute()
const auth = useSalesAuth()

const lead = ref(null)
const isLoading = ref(true)
const activeTab = ref('AI_BRIEFING')
const selectedNewStatus = ref('')
const isUpdatingStatus = ref(false)
const assignModalOpen = ref(false)

const newApp = reactive({
  lenderName: '',
  productRef: '',
  appRef: ''
})

const tabs = computed(() => [
  { id: 'AI_BRIEFING', label: 'AI Underwriting Briefing' },
  { id: 'SNAPSHOT', label: 'Borrower Snapshot & Products' },
  { id: 'NOTES', label: 'Notes', badge: lead.value?.notes?.length || 0 },
  { id: 'TASKS', label: 'Tasks', badge: lead.value?.tasks?.length || 0 },
  { id: 'APPLICATIONS', label: 'Bank Applications', badge: lead.value?.applications?.length || 0 },
  { id: 'AUDIT', label: 'Audit Trail' }
])

const fetchLead = async () => {
  isLoading.value = true
  try {
    const token = localStorage.getItem('credence_sales_token')
    const res = await fetch(`/api/sales/leads/${route.params.id}`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    if (res.ok) {
      lead.value = await res.json()
      selectedNewStatus.value = lead.value.current_status
    }
  } catch (err) {
    console.error('Failed to load lead:', err)
  } finally {
    isLoading.value = false
  }
}

const refreshLead = async () => {
  try {
    const token = localStorage.getItem('credence_sales_token')
    const res = await fetch(`/api/sales/leads/${route.params.id}`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    if (res.ok) {
      lead.value = await res.json()
      selectedNewStatus.value = lead.value.current_status
    }
  } catch (err) {
    console.error('Failed to refresh lead:', err)
  }
}

const handleStatusChange = async () => {
  if (!selectedNewStatus.value || isUpdatingStatus.value) return
  isUpdatingStatus.value = true

  try {
    const token = localStorage.getItem('credence_sales_token')
    const res = await fetch(`/api/sales/leads/${lead.value.id}/status`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        new_status: selectedNewStatus.value,
        reason: `Status updated via Sales Workspace by ${auth.user.value?.name}`
      })
    })

    if (res.ok) {
      await refreshLead()
    }
  } catch (err) {
    console.error('Failed to update status:', err)
  } finally {
    isUpdatingStatus.value = false
  }
}

const submitBankApp = async () => {
  if (!newApp.lenderName.trim()) return
  try {
    const token = localStorage.getItem('credence_sales_token')
    const res = await fetch(`/api/sales/leads/${lead.value.id}/applications`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        lender_name: newApp.lenderName.trim(),
        product_reference: newApp.productRef.trim() || lead.value.loan_category,
        application_reference: newApp.appRef.trim() || null
      })
    })

    if (res.ok) {
      newApp.lenderName = ''
      newApp.productRef = ''
      newApp.appRef = ''
      await refreshLead()
    }
  } catch (err) {
    console.error('Failed to add bank application:', err)
  }
}

const formatCurrency = (val) => {
  if (!val) return '0'
  return Number(val).toLocaleString('en-IN')
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  try {
    const d = new Date(dateStr)
    return d.toLocaleDateString('en-IN', { 
      day: 'numeric', 
      month: 'short', 
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch (e) {
    return dateStr
  }
}

onMounted(() => {
  fetchLead()
})
</script>

