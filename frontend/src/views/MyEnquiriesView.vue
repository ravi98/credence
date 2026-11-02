<template>
  <div class="min-h-screen bg-surface-canvas text-brand-deep flex flex-col">
    <Navbar />

    <main class="flex-1 max-w-5xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
      <!-- Page Header -->
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div>
          <div class="flex items-center gap-2 mb-1">
            <span class="w-2.5 h-2.5 rounded-full bg-sage"></span>
            <span class="text-xs uppercase tracking-wider font-bold text-brand-muted">Customer Portal</span>
          </div>
          <h1 class="text-2xl sm:text-3xl font-extrabold tracking-tight text-brand-deep">
            My Loan Enquiries
          </h1>
          <p class="text-xs sm:text-sm text-brand-muted mt-1 font-medium">
            Track your assisted loan applications, bank evaluations, and specialist assignments.
          </p>
        </div>

        <router-link
          to="/advisor"
          class="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-brand text-white text-xs sm:text-sm font-bold shadow-sm hover:bg-brand-hover transition self-start sm:self-auto"
        >
          <Sparkles class="w-4 h-4 text-sage-light" />
          <span>New Advisor Session</span>
        </router-link>
      </div>

      <!-- Auth Required Gate -->
      <div v-if="!auth.isAuthenticated.value" class="p-8 rounded-3xl bg-white border border-surface-border text-center max-w-md mx-auto shadow-sm space-y-4">
        <div class="w-12 h-12 rounded-2xl bg-surface-light text-brand flex items-center justify-center mx-auto">
          <Lock class="w-6 h-6" />
        </div>
        <div>
          <h3 class="text-lg font-bold text-brand-deep">Sign in to View Your Enquiries</h3>
          <p class="text-xs text-brand-muted mt-1">
            Please log in with your Credence account to inspect your loan applications and status history.
          </p>
        </div>
        <router-link
          to="/login?redirect=/my-enquiries"
          class="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-brand text-white text-xs sm:text-sm font-bold shadow-sm hover:bg-brand-hover transition"
        >
          <span>Sign In / Register</span>
          <ArrowRight class="w-4 h-4" />
        </router-link>
      </div>

      <!-- Loading State -->
      <div v-else-if="isLoading" class="py-16 text-center space-y-3">
        <Loader2 class="w-8 h-8 animate-spin text-brand mx-auto" />
        <p class="text-xs sm:text-sm font-semibold text-brand-muted">Fetching your loan applications...</p>
      </div>

      <!-- Empty State -->
      <div v-else-if="enquiries.length === 0" class="p-10 rounded-3xl bg-white border border-surface-border text-center max-w-lg mx-auto shadow-sm space-y-4">
        <div class="w-14 h-14 rounded-2xl bg-surface-light text-brand flex items-center justify-center mx-auto">
          <FileText class="w-7 h-7" />
        </div>
        <div class="space-y-1">
          <h3 class="text-lg font-bold text-brand-deep">No Loan Enquiries Yet</h3>
          <p class="text-xs sm:text-sm text-brand-muted leading-relaxed">
            You haven't submitted any loan assistance inquiries yet. Ask our AI Loan Advisor or compare verified bank schemes to get assisted at ₹0 fee.
          </p>
        </div>
        <div class="pt-2 flex items-center justify-center gap-3">
          <router-link
            to="/advisor"
            class="px-5 py-2.5 rounded-xl bg-brand text-white text-xs sm:text-sm font-bold shadow-sm hover:bg-brand-hover transition"
          >
            Consult Loan Advisor
          </router-link>
          <router-link
            to="/explore"
            class="px-5 py-2.5 rounded-xl bg-surface-secondary text-brand-deep text-xs sm:text-sm font-semibold hover:bg-surface-border transition"
          >
            Explore Schemes
          </router-link>
        </div>
      </div>

      <!-- Enquiries List -->
      <div v-else class="space-y-4">
        <div 
          v-for="enq in enquiries" 
          :key="enq.id"
          class="p-5 sm:p-6 rounded-2xl bg-white border border-surface-border hover:border-brand/30 transition shadow-2xs space-y-4"
        >
          <!-- Top Row: Reference & Status Pill -->
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-surface-border/60">
            <div class="flex items-center gap-3 flex-wrap">
              <span class="font-mono text-sm sm:text-base font-bold text-brand">
                {{ enq.enquiry_reference }}
              </span>
              <span class="text-xs text-brand-muted font-medium">
                Submitted {{ formatDate(enq.created_at) }}
              </span>
            </div>

            <!-- Status Pill -->
            <span 
              class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold border self-start sm:self-auto"
              :class="getStatusBadgeClass(enq.current_status)"
            >
              <span class="w-1.5 h-1.5 rounded-full" :class="getStatusDotClass(enq.current_status)"></span>
              <span>{{ formatStatusLabel(enq.current_status) }}</span>
            </span>
          </div>

          <!-- Middle Row: Scheme & Amount Details -->
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <span class="text-[10px] uppercase font-bold tracking-wider text-brand-muted block">Selected Scheme</span>
              <p class="font-bold text-brand-deep text-sm sm:text-base mt-0.5">
                {{ enq.primary_product?.scheme_name || 'Retail Loan Scheme' }}
              </p>
              <p class="text-xs text-brand font-semibold">
                {{ enq.primary_product?.institution }} · {{ enq.primary_product?.interest_rate }}
              </p>
            </div>

            <div>
              <span class="text-[10px] uppercase font-bold tracking-wider text-brand-muted block">Requested Quantum</span>
              <p class="font-bold text-brand-deep text-sm sm:text-base mt-0.5 font-tabular">
                ₹{{ formatCurrency(enq.requested_amount) }}
              </p>
              <p class="text-xs text-brand-muted font-medium">
                {{ Math.round((enq.preferred_tenure_months || 240) / 12) }} Years Tenure
              </p>
            </div>

            <div>
              <span class="text-[10px] uppercase font-bold tracking-wider text-brand-muted block">Underwriting Readiness</span>
              <div class="flex items-center gap-1.5 mt-1">
                <span 
                  v-if="enq.summary_status === 'COMPLETED'" 
                  class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-md bg-sage/10 text-sage text-xs font-bold border border-sage/20"
                >
                  <CheckCircle2 class="w-3.5 h-3.5" />
                  AI Briefing Frozen
                </span>
                <span 
                  v-else 
                  class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-md bg-amber-50 text-amber-800 text-xs font-bold border border-amber-200"
                >
                  <Loader2 class="w-3.5 h-3.5 animate-spin" />
                  Analyzing Profile
                </span>
              </div>
            </div>
          </div>

          <!-- Bottom Actions -->
          <div class="pt-2 flex items-center justify-between gap-3">
            <button 
              @click="openDetails(enq.id)"
              class="text-xs font-bold text-brand hover:text-brand-hover flex items-center gap-1 cursor-pointer"
            >
              <span>View Full Application Details</span>
              <ChevronRight class="w-4 h-4" />
            </button>

            <router-link
              to="/advisor"
              class="text-xs text-brand-muted hover:text-brand-deep font-semibold"
            >
              Continue in Advisor →
            </router-link>
          </div>
        </div>
      </div>
    </main>

    <!-- Details Modal / Drawer -->
    <div v-if="detailEnquiry" class="fixed inset-0 z-50 overflow-y-auto bg-black/60 backdrop-blur-xs flex items-center justify-center p-3 sm:p-4">
      <div class="relative w-full max-w-2xl bg-white rounded-3xl shadow-2xl border border-surface-border overflow-hidden max-h-[90vh] flex flex-col">
        <!-- Header -->
        <div class="px-6 py-4 border-b border-surface-border flex items-center justify-between bg-surface-canvas/60">
          <div>
            <span class="text-[10px] uppercase tracking-wider font-bold text-brand-muted block">Enquiry Details</span>
            <h3 class="font-mono text-base sm:text-lg font-bold text-brand">
              {{ detailEnquiry.enquiry_reference }}
            </h3>
          </div>
          <button 
            @click="detailEnquiry = null"
            class="p-2 text-brand-muted hover:text-brand-deep rounded-xl hover:bg-surface-secondary cursor-pointer"
          >
            <X class="w-5 h-5" />
          </button>
        </div>

        <!-- Body -->
        <div class="flex-1 overflow-y-auto p-6 space-y-5 text-xs sm:text-sm">
          <!-- Borrower Snapshot Card -->
          <div class="p-4 rounded-2xl bg-surface-canvas border border-surface-border space-y-2.5">
            <h4 class="font-bold text-xs uppercase tracking-wider text-brand-deep">Verified Borrower Profile Snapshot</h4>
            <div class="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
              <div>
                <span class="text-brand-muted block">Applicant Name:</span>
                <strong class="font-bold text-brand-deep">{{ detailEnquiry.borrower_profile_snapshot?.full_name }}</strong>
              </div>
              <div>
                <span class="text-brand-muted block">Monthly Net Income:</span>
                <strong class="font-bold text-brand-deep font-tabular">₹{{ formatCurrency(detailEnquiry.borrower_profile_snapshot?.monthly_income) }}</strong>
              </div>
              <div>
                <span class="text-brand-muted block">Employment:</span>
                <strong class="font-bold text-brand-deep">{{ detailEnquiry.borrower_profile_snapshot?.employment }}</strong>
              </div>
              <div>
                <span class="text-brand-muted block">City:</span>
                <strong class="font-bold text-brand-deep">{{ detailEnquiry.borrower_profile_snapshot?.city }}</strong>
              </div>
              <div>
                <span class="text-brand-muted block">CIBIL Benchmark:</span>
                <strong class="font-bold text-brand-deep">{{ detailEnquiry.borrower_profile_snapshot?.cibil_score || 750 }}</strong>
              </div>
              <div>
                <span class="text-brand-muted block">Existing EMIs:</span>
                <strong class="font-bold text-brand-deep font-tabular">₹{{ formatCurrency(detailEnquiry.borrower_profile_snapshot?.existing_emi || 0) }}</strong>
              </div>
            </div>
          </div>

          <!-- Selected Products -->
          <div class="space-y-2">
            <h4 class="font-bold text-xs uppercase tracking-wider text-brand-deep">Evaluated Bank Products</h4>
            <div 
              v-for="p in detailEnquiry.products" 
              :key="p.id"
              class="p-3.5 rounded-xl border border-surface-border flex items-center justify-between gap-3"
            >
              <div>
                <span class="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-md" :class="p.preference_type === 'PRIMARY' ? 'bg-brand/10 text-brand' : 'bg-surface-secondary text-brand-muted'">
                  {{ p.preference_type }}
                </span>
                <h5 class="font-bold text-brand-deep text-sm mt-1">{{ p.scheme_name }}</h5>
                <p class="text-xs text-brand-muted font-medium">{{ p.institution }} · {{ p.product_snapshot?.interest_rate_range || 'Market Rate' }}</p>
              </div>
              <span class="text-xs font-semibold text-brand-muted">Max {{ p.product_snapshot?.max_tenure_years || 30 }} Yrs</span>
            </div>
          </div>

          <!-- Audit Timeline -->
          <div v-if="detailEnquiry.status_history?.length > 0" class="space-y-2">
            <h4 class="font-bold text-xs uppercase tracking-wider text-brand-deep">Application Lifecycle Audit Log</h4>
            <div class="space-y-2 text-xs">
              <div 
                v-for="h in detailEnquiry.status_history" 
                :key="h.id"
                class="p-2.5 rounded-lg bg-surface-secondary/60 flex items-center justify-between"
              >
                <div class="flex items-center gap-2">
                  <span class="font-bold text-brand-deep">{{ formatStatusLabel(h.new_status) }}</span>
                  <span class="text-brand-muted">— {{ h.reason }}</span>
                </div>
                <span class="text-brand-muted text-[11px] font-mono">{{ formatDate(h.created_at) }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Footer -->
        <div class="px-6 py-3 border-t border-surface-border bg-surface-canvas/60 text-right">
          <button 
            @click="detailEnquiry = null"
            class="px-5 py-2 rounded-xl bg-brand text-white text-xs font-bold hover:bg-brand-hover transition cursor-pointer"
          >
            Close
          </button>
        </div>
      </div>
    </div>

    <Footer />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { 
  Sparkles, 
  Lock, 
  ArrowRight, 
  Loader2, 
  FileText, 
  CheckCircle2, 
  ChevronRight, 
  X 
} from 'lucide-vue-next'
import Navbar from '../components/Navbar.vue'
import Footer from '../components/Footer.vue'
import { useAuth } from '../auth.js'

const auth = useAuth()
const enquiries = ref([])
const isLoading = ref(true)
const detailEnquiry = ref(null)

const fetchMyEnquiries = async () => {
  if (!auth.isAuthenticated.value) {
    isLoading.value = false
    return
  }

  isLoading.value = true
  try {
    const token = localStorage.getItem('credence_token')
    const res = await fetch('/api/enquiries/my', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    if (res.ok) {
      const data = await res.json()
      enquiries.value = data.enquiries || []
    }
  } catch (err) {
    console.error('Failed to load enquiries:', err)
  } finally {
    isLoading.value = false
  }
}

const openDetails = async (id) => {
  try {
    const token = localStorage.getItem('credence_token')
    const res = await fetch(`/api/enquiries/${id}`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    if (res.ok) {
      detailEnquiry.value = await res.json()
    }
  } catch (err) {
    console.error('Failed to load enquiry details:', err)
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
    return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
  } catch (e) {
    return dateStr
  }
}

const formatStatusLabel = (status) => {
  const map = {
    'NEW': 'Application Submitted',
    'ASSIGNED': 'Specialist Assigned',
    'CONTACT_ATTEMPTED': 'Contact Attempted',
    'CONTACTED': 'In Discussion',
    'QUALIFIED': 'Bank Verification In-Progress',
    'NOT_QUALIFIED': 'Ineligible at Present',
    'CLOSED_LOST': 'Closed'
  }
  return map[status] || status
}

const getStatusBadgeClass = (status) => {
  const map = {
    'NEW': 'bg-blue-50 text-blue-800 border-blue-200',
    'ASSIGNED': 'bg-amber-50 text-amber-800 border-amber-200',
    'CONTACT_ATTEMPTED': 'bg-slate-50 text-slate-800 border-slate-200',
    'CONTACTED': 'bg-teal-50 text-teal-800 border-teal-200',
    'QUALIFIED': 'bg-sage/10 text-sage border-sage/20',
    'NOT_QUALIFIED': 'bg-rose-50 text-rose-800 border-rose-200',
    'CLOSED_LOST': 'bg-gray-100 text-gray-700 border-gray-200'
  }
  return map[status] || 'bg-surface-secondary text-brand-deep border-surface-border'
}

const getStatusDotClass = (status) => {
  const map = {
    'NEW': 'bg-blue-600',
    'ASSIGNED': 'bg-amber-600',
    'CONTACT_ATTEMPTED': 'bg-slate-600',
    'CONTACTED': 'bg-teal-600',
    'QUALIFIED': 'bg-sage',
    'NOT_QUALIFIED': 'bg-rose-600',
    'CLOSED_LOST': 'bg-gray-500'
  }
  return map[status] || 'bg-brand'
}

onMounted(() => {
  fetchMyEnquiries()
})
</script>

