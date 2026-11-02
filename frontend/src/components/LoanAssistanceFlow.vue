<template>
  <div v-if="isOpen" class="fixed inset-0 z-50 overflow-y-auto bg-black/60 backdrop-blur-xs flex items-center justify-center p-3 sm:p-4">
    <div 
      class="relative w-full max-w-2xl bg-white rounded-3xl shadow-2xl border border-surface-border overflow-hidden transition-all flex flex-col max-h-[92vh]"
      @click.stop
    >
      <!-- Modal Header -->
      <div class="px-6 py-4.5 border-b border-surface-border flex items-center justify-between bg-surface-canvas/60">
        <div class="flex items-center gap-2.5">
          <div class="w-8 h-8 rounded-xl bg-brand text-white flex items-center justify-center font-bold text-sm shadow-2xs">
            <ShieldCheck class="w-4 h-4 text-sage-light" />
          </div>
          <div>
            <h3 class="font-bold text-base sm:text-lg text-brand-deep leading-tight">
              Credence Loan Assistance
            </h3>
            <p class="text-xs text-brand-muted font-medium">
              Verified Banking Guidance · ₹0 Advisory Fee
            </p>
          </div>
        </div>

        <button 
          @click="close"
          class="p-2 text-brand-muted hover:text-brand-deep rounded-xl hover:bg-surface-secondary transition cursor-pointer"
        >
          <X class="w-5 h-5" />
        </button>
      </div>

      <!-- Step Indicator (Only during stage 1 & 2) -->
      <div v-if="currentStage !== 'CONFIRMATION'" class="px-6 py-3 bg-surface-secondary/40 border-b border-surface-border flex items-center justify-between text-xs font-semibold">
        <div class="flex items-center gap-2" :class="currentStage === 'DETAILS' ? 'text-brand font-bold' : 'text-sage'">
          <span class="w-5 h-5 rounded-full flex items-center justify-center text-[11px]" :class="currentStage === 'DETAILS' ? 'bg-brand text-white' : 'bg-sage text-white'">
            <Check v-if="currentStage === 'CONSENTS'" class="w-3 h-3" />
            <span v-else>1</span>
          </span>
          <span>Borrower Details</span>
        </div>
        <div class="h-0.5 w-12 bg-surface-border"></div>
        <div class="flex items-center gap-2" :class="currentStage === 'CONSENTS' ? 'text-brand font-bold' : 'text-brand-muted'">
          <span class="w-5 h-5 rounded-full flex items-center justify-center text-[11px]" :class="currentStage === 'CONSENTS' ? 'bg-brand text-white' : 'bg-surface-border text-brand-muted'">
            2
          </span>
          <span>Preferences & Consents</span>
        </div>
      </div>

      <!-- Scrollable Form Body -->
      <div class="flex-1 overflow-y-auto p-5 sm:p-6 space-y-5">
        <!-- Error Message Alert -->
        <div v-if="errorMessage" class="p-3.5 rounded-xl bg-red-50 border border-red-200 text-red-800 text-xs sm:text-sm flex items-start gap-2.5">
          <AlertCircle class="w-4 h-4 flex-shrink-0 mt-0.5 text-red-600" />
          <div class="flex-1 font-medium">{{ errorMessage }}</div>
        </div>

        <!-- ==================== STAGE 1: BORROWER DETAILS ==================== -->
        <div v-if="currentStage === 'DETAILS'" class="space-y-4">
          <!-- Primary Selected Loan Scheme Card -->
          <div class="p-4 rounded-2xl bg-surface-light border border-brand/20">
            <span class="text-[10px] uppercase font-bold tracking-wider text-brand-muted block mb-1">
              Primary Selected Scheme
            </span>
            <div class="flex items-start justify-between gap-3">
              <div>
                <h4 class="font-bold text-brand-deep text-base">
                  {{ primaryProduct.scheme_name }}
                </h4>
                <p class="text-xs text-brand font-semibold mt-0.5">
                  {{ primaryProduct.institution }} · {{ primaryProduct.interest_rate }}
                </p>
              </div>
              <span class="px-2.5 py-1 rounded-lg bg-sage/10 text-sage text-xs font-bold border border-sage/20 whitespace-nowrap">
                Grounded Rate
              </span>
            </div>

            <!-- Alternate Schemes Selector if Available -->
            <div v-if="availableAlternatives.length > 0" class="mt-3 pt-3 border-t border-brand/15">
              <span class="text-xs font-semibold text-brand-deep block mb-1.5">
                Also compare with alternate recommendations:
              </span>
              <div class="space-y-1.5">
                <label 
                  v-for="alt in availableAlternatives" 
                  :key="alt.slug" 
                  class="flex items-center gap-2.5 text-xs text-brand-deep cursor-pointer p-1.5 rounded-lg hover:bg-white/60 transition"
                >
                  <input 
                    type="checkbox" 
                    :value="alt.slug" 
                    v-model="selectedAlternativeSlugs"
                    class="rounded text-brand focus:ring-brand"
                  />
                  <span class="font-medium">{{ alt.scheme_name }} ({{ alt.institution }})</span>
                </label>
              </div>
            </div>
          </div>

          <!-- Form Fields Grid -->
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
            <!-- Full Name -->
            <div>
              <label class="block text-xs font-bold text-brand-deep mb-1">Full Legal Name *</label>
              <input 
                v-model="formData.fullName"
                type="text" 
                placeholder="e.g. Rahul Sharma"
                class="w-full text-xs sm:text-sm px-3.5 py-2.5 rounded-xl border border-surface-border focus:border-brand focus:ring-1 focus:ring-brand outline-none"
              />
            </div>

            <!-- Phone Number -->
            <div>
              <label class="block text-xs font-bold text-brand-deep mb-1">Mobile Number (10 digits) *</label>
              <div class="relative flex items-center">
                <span class="absolute left-3 text-xs text-brand-muted font-bold">+91</span>
                <input 
                  v-model="formData.phone"
                  type="tel" 
                  maxlength="10"
                  placeholder="9876543210"
                  class="w-full text-xs sm:text-sm pl-11 pr-3.5 py-2.5 rounded-xl border border-surface-border focus:border-brand focus:ring-1 focus:ring-brand outline-none"
                />
              </div>
            </div>

            <!-- Email -->
            <div>
              <label class="block text-xs font-bold text-brand-deep mb-1">Email Address *</label>
              <input 
                v-model="formData.email"
                type="email" 
                placeholder="rahul@example.com"
                class="w-full text-xs sm:text-sm px-3.5 py-2.5 rounded-xl border border-surface-border focus:border-brand focus:ring-1 focus:ring-brand outline-none"
              />
            </div>

            <!-- City -->
            <div>
              <label class="block text-xs font-bold text-brand-deep mb-1">Current City *</label>
              <input 
                v-model="formData.city"
                type="text" 
                placeholder="e.g. Mumbai, Bengaluru"
                class="w-full text-xs sm:text-sm px-3.5 py-2.5 rounded-xl border border-surface-border focus:border-brand focus:ring-1 focus:ring-brand outline-none"
              />
            </div>

            <!-- Employment Type -->
            <div>
              <label class="block text-xs font-bold text-brand-deep mb-1">Employment Type *</label>
              <select 
                v-model="formData.employment"
                class="w-full text-xs sm:text-sm px-3.5 py-2.5 rounded-xl border border-surface-border focus:border-brand focus:ring-1 focus:ring-brand outline-none bg-white"
              >
                <option value="Salaried">Salaried (MNC / Corporate / Govt)</option>
                <option value="Self-Employed Professional">Self-Employed Professional (Doctor/CA/Lawyer)</option>
                <option value="Self-Employed Business">Self-Employed Business / Proprietor</option>
                <option value="Other">Other / Retired</option>
              </select>
            </div>

            <!-- Company Name -->
            <div>
              <label class="block text-xs font-bold text-brand-deep mb-1">Employer / Business Name</label>
              <input 
                v-model="formData.companyName"
                type="text" 
                placeholder="e.g. Infosys, TCS, Clinic"
                class="w-full text-xs sm:text-sm px-3.5 py-2.5 rounded-xl border border-surface-border focus:border-brand focus:ring-1 focus:ring-brand outline-none"
              />
            </div>

            <!-- Monthly Income -->
            <div>
              <label class="block text-xs font-bold text-brand-deep mb-1">Net Monthly Take-Home (₹) *</label>
              <input 
                v-model.number="formData.monthlyIncome"
                type="number" 
                step="5000"
                placeholder="e.g. 85000"
                class="w-full text-xs sm:text-sm px-3.5 py-2.5 rounded-xl border border-surface-border focus:border-brand focus:ring-1 focus:ring-brand outline-none"
              />
            </div>

            <!-- Requested Loan Amount -->
            <div>
              <label class="block text-xs font-bold text-brand-deep mb-1">Requested Loan Amount (₹) *</label>
              <input 
                v-model.number="formData.requestedAmount"
                type="number" 
                step="50000"
                placeholder="e.g. 5000000"
                class="w-full text-xs sm:text-sm px-3.5 py-2.5 rounded-xl border border-surface-border focus:border-brand focus:ring-1 focus:ring-brand outline-none"
              />
            </div>

            <!-- Preferred Tenure -->
            <div>
              <label class="block text-xs font-bold text-brand-deep mb-1">Preferred Tenure (Years) *</label>
              <input 
                v-model.number="formData.tenureYears"
                type="number" 
                min="1" 
                max="30"
                class="w-full text-xs sm:text-sm px-3.5 py-2.5 rounded-xl border border-surface-border focus:border-brand focus:ring-1 focus:ring-brand outline-none"
              />
            </div>

            <!-- Existing Monthly EMIs -->
            <div>
              <label class="block text-xs font-bold text-brand-deep mb-1">Existing Monthly EMIs (₹)</label>
              <input 
                v-model.number="formData.existingEmi"
                type="number" 
                placeholder="0"
                class="w-full text-xs sm:text-sm px-3.5 py-2.5 rounded-xl border border-surface-border focus:border-brand focus:ring-1 focus:ring-brand outline-none"
              />
            </div>
          </div>
        </div>

        <!-- ==================== STAGE 2: CONTACT PREFERENCES & CONSENTS ==================== -->
        <div v-if="currentStage === 'CONSENTS'" class="space-y-4">
          <!-- Contact Preferences -->
          <div class="p-4 rounded-2xl bg-surface-canvas border border-surface-border space-y-3">
            <h4 class="text-xs font-bold uppercase tracking-wider text-brand-deep">
              Contact Preferences
            </h4>

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label class="block text-xs font-semibold text-brand-muted mb-1">Preferred Channel</label>
                <select 
                  v-model="formData.preferredChannel"
                  class="w-full text-xs sm:text-sm px-3 py-2 rounded-xl border border-surface-border bg-white"
                >
                  <option value="WhatsApp">WhatsApp (Fastest response)</option>
                  <option value="Phone Call">Direct Phone Call</option>
                  <option value="Email">Email Consultation</option>
                </select>
              </div>

              <div>
                <label class="block text-xs font-semibold text-brand-muted mb-1">Best Time to Connect</label>
                <select 
                  v-model="formData.preferredTimeSlot"
                  class="w-full text-xs sm:text-sm px-3 py-2 rounded-xl border border-surface-border bg-white"
                >
                  <option value="Morning (10 AM - 1 PM)">Morning (10:00 AM - 1:00 PM)</option>
                  <option value="Afternoon (1 PM - 5 PM)">Afternoon (1:00 PM - 5:00 PM)</option>
                  <option value="Evening (5 PM - 8 PM)">Evening (5:00 PM - 8:00 PM)</option>
                </select>
              </div>
            </div>

            <div>
              <label class="block text-xs font-semibold text-brand-muted mb-1">Special Notes / Urgent Requirements</label>
              <textarea 
                v-model="formData.notes"
                rows="2"
                placeholder="e.g. Property already identified, need quick sanction in 5 days."
                class="w-full text-xs sm:text-sm p-2.5 rounded-xl border border-surface-border focus:border-brand outline-none"
              ></textarea>
            </div>
          </div>

          <!-- DPDP & Fair Practices Consents -->
          <div class="p-4 rounded-2xl bg-surface-secondary/50 border border-surface-border space-y-3">
            <div class="flex items-center gap-2">
              <ShieldCheck class="w-4 h-4 text-sage" />
              <h4 class="text-xs font-bold uppercase tracking-wider text-brand-deep">
                Regulatory Consents (DPDP Act & RBI Compliant)
              </h4>
            </div>

            <div class="space-y-3 text-xs text-brand-deep">
              <!-- Consent 1: Credence Specialist (Required) -->
              <label class="flex items-start gap-2.5 cursor-pointer">
                <input 
                  type="checkbox" 
                  v-model="formData.consentSpecialist"
                  class="mt-0.5 rounded text-brand focus:ring-brand"
                />
                <span class="font-medium">
                  <strong class="font-bold text-brand-deep">Credence Specialist Consultation (Required):</strong>
                  I authorize a dedicated Credence loan specialist to contact me via phone, WhatsApp, or email to assist with this application.
                </span>
              </label>

              <!-- Consent 2: Lender Data Sharing (Required) -->
              <label class="flex items-start gap-2.5 cursor-pointer">
                <input 
                  type="checkbox" 
                  v-model="formData.consentLenderSharing"
                  class="mt-0.5 rounded text-brand focus:ring-brand"
                />
                <span class="font-medium">
                  <strong class="font-bold text-brand-deep">Lender Verification & Eligibility (Required):</strong>
                  I authorize Credence to share my submitted borrowing profile and eligibility parameters with partner banks and NBFCs to obtain sanctioned in-principle offers.
                </span>
              </label>

              <!-- Consent 3: Rate Alerts (Optional) -->
              <label class="flex items-start gap-2.5 cursor-pointer">
                <input 
                  type="checkbox" 
                  v-model="formData.consentMarketing"
                  class="mt-0.5 rounded text-brand focus:ring-brand"
                />
                <span class="font-medium text-brand-muted">
                  <strong class="font-bold text-brand-deep">Rate & Policy Alerts (Optional):</strong>
                  Keep me updated on interest rate adjustments, repo-rate cuts, and balance transfer opportunities.
                </span>
              </label>
            </div>
          </div>

          <!-- If User Not Authenticated: Quick inline login / register -->
          <div v-if="!auth.isAuthenticated.value" class="p-4 rounded-2xl bg-amber-50/60 border border-amber-200 space-y-2.5">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold text-amber-900">
                Create Account to Track Application
              </span>
              <span class="text-[11px] text-amber-700 font-medium">Takes 5 seconds</span>
            </div>
            <p class="text-[11px] text-amber-800 leading-snug">
              Set a quick password so you can track your application status, inspect bank offers, and chat with your loan officer.
            </p>
            <input 
              v-model="accountPassword"
              type="password" 
              placeholder="Create a password (min 6 characters)"
              class="w-full text-xs sm:text-sm px-3 py-2 rounded-xl border border-amber-300 bg-white focus:outline-none focus:ring-1 focus:ring-amber-500"
            />
          </div>
        </div>

        <!-- ==================== STAGE 3: CONFIRMATION ==================== -->
        <div v-if="currentStage === 'CONFIRMATION'" class="py-4 space-y-6 text-center">
          <div class="w-16 h-16 rounded-full bg-sage/10 text-sage flex items-center justify-center mx-auto border-2 border-sage/20">
            <CheckCircle2 class="w-8 h-8" />
          </div>

          <div class="space-y-1">
            <h3 class="text-xl font-bold text-brand-deep">Application Submitted!</h3>
            <p class="text-xs sm:text-sm text-brand-muted max-w-md mx-auto">
              Your loan enquiry has been registered and frozen with full conversational context.
            </p>
          </div>

          <!-- Reference Number Card -->
          <div class="p-4 rounded-2xl bg-surface-canvas border border-surface-border max-w-sm mx-auto flex items-center justify-between gap-3">
            <div class="text-left">
              <span class="text-[10px] uppercase font-bold text-brand-muted block">Enquiry Reference</span>
              <span class="text-base sm:text-lg font-mono font-bold text-brand">{{ submittedReference }}</span>
            </div>
            <button 
              @click="copyReference"
              class="p-2 rounded-lg hover:bg-surface-secondary text-brand-muted hover:text-brand-deep transition text-xs font-semibold flex items-center gap-1.5 cursor-pointer"
            >
              <Check v-if="copiedRef" class="w-4 h-4 text-sage" />
              <Copy v-else class="w-4 h-4" />
              <span>{{ copiedRef ? 'Copied' : 'Copy' }}</span>
            </button>
          </div>

          <!-- Step Progression Timeline -->
          <div class="max-w-md mx-auto text-left space-y-3 pt-2">
            <h4 class="text-xs font-bold uppercase tracking-wider text-brand-muted">What Happens Next?</h4>
            
            <div class="space-y-2.5 text-xs text-brand-deep">
              <div class="flex items-start gap-3">
                <span class="w-5 h-5 rounded-full bg-sage text-white flex items-center justify-center font-bold text-[10px] flex-shrink-0 mt-0.5">✓</span>
                <div>
                  <strong class="font-bold">AI Underwriting Handoff Generated:</strong>
                  <p class="text-brand-muted text-[11px]">Your requirements and catalog benchmark are analyzed and frozen for underwriting.</p>
                </div>
              </div>

              <div class="flex items-start gap-3">
                <span class="w-5 h-5 rounded-full bg-brand text-white flex items-center justify-center font-bold text-[10px] flex-shrink-0 mt-0.5">2</span>
                <div>
                  <strong class="font-bold">Specialist Assignment (Within 2 Hours):</strong>
                  <p class="text-brand-muted text-[11px]">A certified Credence loan officer will contact you via {{ formData.preferredChannel }}.</p>
                </div>
              </div>

              <div class="flex items-start gap-3">
                <span class="w-5 h-5 rounded-full bg-surface-border text-brand-muted flex items-center justify-center font-bold text-[10px] flex-shrink-0 mt-0.5">3</span>
                <div>
                  <strong class="font-bold">Expedited Bank Sanction:</strong>
                  <p class="text-brand-muted text-[11px]">Doorstep document pickup, lender negotiation, and direct disbursement tracking.</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Modal Footer Actions -->
      <div class="px-6 py-4 border-t border-surface-border bg-surface-canvas/60 flex items-center justify-between">
        <div v-if="currentStage === 'DETAILS'">
          <button 
            @click="close"
            class="text-xs sm:text-sm font-semibold text-brand-muted hover:text-brand-deep px-3 py-2 cursor-pointer"
          >
            Cancel
          </button>
        </div>

        <div v-else-if="currentStage === 'CONSENTS'">
          <button 
            @click="currentStage = 'DETAILS'"
            class="text-xs sm:text-sm font-semibold text-brand-deep px-3 py-2 hover:bg-surface-secondary rounded-xl transition cursor-pointer"
          >
            ← Back
          </button>
        </div>

        <div v-else-if="currentStage === 'CONFIRMATION'" class="w-full flex items-center justify-between gap-3">
          <button 
            @click="close"
            class="text-xs sm:text-sm font-semibold text-brand-deep px-4 py-2 hover:bg-surface-secondary rounded-xl transition cursor-pointer"
          >
            Continue Chatting
          </button>
          <router-link 
            to="/my-enquiries"
            @click="close"
            class="px-5 py-2.5 rounded-xl bg-brand text-white text-xs sm:text-sm font-bold shadow-sm hover:bg-brand-hover transition flex items-center gap-1.5"
          >
            <span>View My Enquiries</span>
            <ArrowRight class="w-4 h-4" />
          </router-link>
        </div>

        <!-- Next / Submit Buttons -->
        <div v-if="currentStage === 'DETAILS'">
          <button 
            @click="proceedToConsents"
            class="px-5 py-2.5 rounded-xl bg-brand text-white text-xs sm:text-sm font-bold shadow-sm hover:bg-brand-hover transition flex items-center gap-1.5 cursor-pointer"
          >
            <span>Next: Preferences</span>
            <ArrowRight class="w-4 h-4" />
          </button>
        </div>

        <div v-else-if="currentStage === 'CONSENTS'">
          <button 
            @click="submitEnquiry"
            :disabled="isSubmitting"
            class="px-6 py-2.5 rounded-xl bg-brand text-white text-xs sm:text-sm font-bold shadow-sm hover:bg-brand-hover disabled:opacity-50 transition flex items-center gap-2 cursor-pointer"
          >
            <Loader2 v-if="isSubmitting" class="w-4 h-4 animate-spin" />
            <span>{{ isSubmitting ? 'Submitting Application...' : 'Submit Loan Enquiry' }}</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { 
  ShieldCheck, 
  X, 
  Check, 
  ArrowRight, 
  AlertCircle, 
  CheckCircle2, 
  Copy, 
  Loader2 
} from 'lucide-vue-next'
import { useAuth } from '../auth.js'

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  },
  candidate: {
    type: Object,
    default: null
  },
  allCandidates: {
    type: Array,
    default: () => []
  },
  userProfile: {
    type: Object,
    default: () => ({})
  },
  conversationId: {
    type: String,
    default: null
  }
})

const emit = defineEmits(['close', 'submitted'])
const auth = useAuth()

const currentStage = ref('DETAILS') // 'DETAILS' | 'CONSENTS' | 'CONFIRMATION'
const errorMessage = ref('')
const isSubmitting = ref(false)
const submittedReference = ref('')
const copiedRef = ref(false)
const accountPassword = ref('')
const selectedAlternativeSlugs = ref([])

const formData = reactive({
  fullName: '',
  phone: '',
  email: '',
  city: 'Mumbai',
  employment: 'Salaried',
  companyName: '',
  monthlyIncome: 85000,
  requestedAmount: 5000000,
  tenureYears: 20,
  existingEmi: 0,
  preferredChannel: 'WhatsApp',
  preferredTimeSlot: 'Morning (10 AM - 1 PM)',
  notes: '',
  consentSpecialist: true,
  consentLenderSharing: true,
  consentMarketing: false
})

const primaryProduct = computed(() => {
  if (props.candidate?.metadata) {
    return {
      slug: props.candidate.metadata.compact_key || props.candidate.metadata.scheme_slug || 'loan-scheme',
      scheme_name: props.candidate.metadata.scheme_name || 'Retail Loan Scheme',
      institution: props.candidate.metadata.institution || 'Partner Bank',
      interest_rate: props.candidate.metadata.interest_rate_range || 'Competitive Rate'
    }
  }
  return {
    slug: 'retail-loan',
    scheme_name: 'Selected Retail Loan Scheme',
    institution: 'Credence Banking Partner',
    interest_rate: 'Market Linked'
  }
})

const availableAlternatives = computed(() => {
  if (!props.allCandidates || props.allCandidates.length <= 1) return []
  return props.allCandidates.slice(1, 3).map(c => ({
    slug: c.metadata?.compact_key || c.metadata?.scheme_slug,
    scheme_name: c.metadata?.scheme_name || 'Alternate Scheme',
    institution: c.metadata?.institution || 'Bank'
  })).filter(a => !!a.slug)
})

// Initialize form from props & auth whenever modal opens
watch(() => props.isOpen, (open) => {
  if (open) {
    currentStage.value = 'DETAILS'
    errorMessage.value = ''
    isSubmitting.value = false
    copiedRef.value = false

    // Pre-fill user data
    if (auth.user.value) {
      formData.fullName = auth.user.value.name || formData.fullName
      formData.email = auth.user.value.email || formData.email
    }

    if (props.userProfile) {
      if (props.userProfile.employment) formData.employment = props.userProfile.employment
      if (props.userProfile.income) {
        const num = parseFloat(String(props.userProfile.income).replace(/[^0-9.]/g, ''))
        if (num > 0) formData.monthlyIncome = num
      }
      if (props.userProfile.requested_amount) {
        const num = parseFloat(String(props.userProfile.requested_amount).replace(/[^0-9.]/g, ''))
        if (num > 0) formData.requestedAmount = num
      }
    }
  }
})

const proceedToConsents = () => {
  errorMessage.value = ''

  if (!formData.fullName.trim() || formData.fullName.trim().length < 2) {
    errorMessage.value = 'Please provide your full legal name.'
    return
  }

  const cleanPhone = formData.phone.replace(/[^0-9]/g, '')
  if (cleanPhone.length !== 10) {
    errorMessage.value = 'Please provide a valid 10-digit Indian mobile number.'
    return
  }

  if (!formData.email.trim() || !formData.email.includes('@')) {
    errorMessage.value = 'Please provide a valid email address.'
    return
  }

  if (!formData.monthlyIncome || formData.monthlyIncome <= 0) {
    errorMessage.value = 'Please provide your net monthly income.'
    return
  }

  if (!formData.requestedAmount || formData.requestedAmount <= 0) {
    errorMessage.value = 'Please provide your requested loan amount.'
    return
  }

  currentStage.value = 'CONSENTS'
}

const submitEnquiry = async () => {
  errorMessage.value = ''

  if (!formData.consentSpecialist || !formData.consentLenderSharing) {
    errorMessage.value = 'Mandatory regulatory consents must be accepted to submit.'
    return
  }

  isSubmitting.value = true

  try {
    // 1. If not authenticated, create account or login first
    if (!auth.isAuthenticated.value) {
      const pwd = accountPassword.value.trim() || `Cred_${Math.random().toString(36).substring(2, 8)}!`
      try {
        await auth.register(formData.fullName, formData.email, pwd)
      } catch (regErr) {
        // If account exists, prompt user or continue
        if (regErr.message?.includes('already exists')) {
          errorMessage.value = 'An account with this email already exists. Please sign in or use another email.'
          isSubmitting.value = false
          return
        }
        throw regErr
      }
    }

    const token = localStorage.getItem('credence_token')

    // 2. Prepare payload
    const altProducts = selectedAlternativeSlugs.value.map(slug => {
      const match = availableAlternatives.value.find(a => a.slug === slug)
      return {
        slug_or_name: slug,
        institution: match?.institution || 'Alternative Bank',
        scheme_name: match?.scheme_name || slug
      }
    })

    const payload = {
      conversation_id: props.conversationId,
      primary_product: {
        slug_or_name: primaryProduct.value.slug,
        institution: primaryProduct.value.institution,
        scheme_name: primaryProduct.value.scheme_name
      },
      alternative_products: altProducts,
      borrower_details: {
        full_name: formData.fullName,
        phone: formData.phone,
        email: formData.email,
        employment: formData.employment,
        monthly_income: Number(formData.monthlyIncome),
        requested_amount: Number(formData.requestedAmount),
        preferred_tenure_months: Number(formData.tenureYears) * 12,
        city: formData.city,
        company_name: formData.companyName || null,
        existing_emi: Number(formData.existingEmi) || 0,
        cibil_score: props.userProfile?.cibil_score || 750,
        category: props.userProfile?.category !== 'All' ? props.userProfile?.category : 'Home Loan'
      },
      contact_preferences: {
        preferred_channel: formData.preferredChannel,
        preferred_time_slot: formData.preferredTimeSlot,
        notes: formData.notes || null
      },
      consents: [
        { purpose: 'CREDENCE_CONTACT', granted: formData.consentSpecialist },
        { purpose: 'LENDER_DATA_SHARING', granted: formData.consentLenderSharing },
        { purpose: 'MARKETING_COMMUNICATION', granted: formData.consentMarketing }
      ]
    }

    const res = await fetch('/api/enquiries', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(payload)
    })

    const data = await res.json()
    if (!res.ok) {
      throw new Error(data.detail || 'Failed to submit loan enquiry.')
    }

    submittedReference.value = data.enquiry_reference
    currentStage.value = 'CONFIRMATION'
    emit('submitted', data)
  } catch (err) {
    errorMessage.value = err.message || 'Submission error. Please check your network connection.'
  } finally {
    isSubmitting.value = false
  }
}

const copyReference = async () => {
  if (!submittedReference.value) return
  await navigator.clipboard.writeText(submittedReference.value)
  copiedRef.value = true
  setTimeout(() => {
    copiedRef.value = false
  }, 2000)
}

const close = () => {
  emit('close')
}
</script>

