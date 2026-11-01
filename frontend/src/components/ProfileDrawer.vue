<template>
  <div 
    class="fixed inset-y-0 right-0 w-80 sm:w-96 bg-white border-l border-surface-border shadow-2xl z-30 flex flex-col transition-transform duration-300 ease-in-out"
    :class="isOpen ? 'translate-x-0' : 'translate-x-full'"
  >
    <!-- Header -->
    <div class="p-4 border-b border-surface-border flex items-center justify-between bg-surface-canvas">
      <div class="flex items-center gap-2">
        <SlidersHorizontal class="w-4 h-4 text-brand" />
        <h3 class="text-sm font-bold text-brand-deep">Borrower Profile & Filters</h3>
      </div>
      <button 
        @click="$emit('close')" 
        class="p-1.5 text-brand-muted hover:text-brand-deep rounded-md hover:bg-surface-secondary transition"
        title="Close profile drawer"
      >
        <X class="w-4 h-4" />
      </button>
    </div>

    <!-- Content -->
    <div class="flex-1 overflow-y-auto p-4 space-y-4 text-xs">
      <div class="bg-surface-light p-3 rounded-lg border border-brand/20 text-brand text-[11px] leading-relaxed">
        <strong>🛡️ Privacy Protection:</strong> Your profile details are used strictly in-memory to estimate FOIR thresholds and scheme qualification. We never sell your data.
      </div>

      <!-- Loan Category -->
      <div>
        <label class="block font-semibold text-brand-deep mb-1">Target Loan Category</label>
        <select 
          :value="profile.category" 
          @change="update('category', $event.target.value)"
          class="w-full bg-surface-canvas border border-surface-border rounded-lg px-3 py-2 text-xs text-brand-deep focus:outline-none focus:border-brand"
        >
          <option value="All">All Categories</option>
          <option value="Home Loan">Home Loan</option>
          <option value="Personal Loan">Personal Loan</option>
          <option value="Education Loan">Education Loan</option>
          <option value="Vehicle Loan">Vehicle Loan</option>
        </select>
      </div>

      <!-- Banking Sector -->
      <div>
        <label class="block font-semibold text-brand-deep mb-1">Banking Sector Preference</label>
        <select 
          :value="profile.sector" 
          @change="update('sector', $event.target.value)"
          class="w-full bg-surface-canvas border border-surface-border rounded-lg px-3 py-2 text-xs text-brand-deep focus:outline-none focus:border-brand"
        >
          <option value="All">All Sectors (34 Institutions)</option>
          <option value="Public">Public Sector Banks (SBI, BoB, Canara, PNB)</option>
          <option value="Private">Private Banks (HDFC, ICICI, Axis, Kotak)</option>
          <option value="NBFC">NBFCs (Bajaj, Tata Capital, L&T)</option>
          <option value="Co-operative">Co-operative Banks</option>
        </select>
      </div>

      <!-- Employment Type -->
      <div>
        <label class="block font-semibold text-brand-deep mb-1">Employment Type</label>
        <select 
          :value="profile.employment" 
          @change="update('employment', $event.target.value)"
          class="w-full bg-surface-canvas border border-surface-border rounded-lg px-3 py-2 text-xs text-brand-deep focus:outline-none focus:border-brand"
        >
          <option value="Salaried">Salaried</option>
          <option value="Self-Employed / Business">Self-Employed / Business</option>
          <option value="Student">Student (Education Loans)</option>
          <option value="Pensioner">Pensioner</option>
          <option value="Doctor / Professional">Doctor / Healthcare Professional</option>
          <option value="Other">Other</option>
        </select>
      </div>

      <!-- CIBIL Credit Score Slider -->
      <div class="bg-surface-canvas p-3 rounded-lg border border-surface-border">
        <div class="flex justify-between items-center mb-1">
          <span class="font-semibold text-brand-deep">Estimated CIBIL Score</span>
          <span class="font-bold font-mono text-sm" :class="scoreColor">{{ profile.cibil_score }}</span>
        </div>
        <input 
          type="range" 
          min="300" 
          max="900" 
          step="5"
          :value="profile.cibil_score" 
          @input="update('cibil_score', Number($event.target.value))"
          class="w-full accent-brand bg-surface-secondary h-2 rounded-lg appearance-none cursor-pointer mt-1"
        />
        <div class="flex justify-between text-[10px] text-brand-muted mt-1">
          <span>300</span>
          <span>750 (Prime Standard)</span>
          <span>900</span>
        </div>
      </div>

      <!-- Monthly Income -->
      <div>
        <label class="block font-semibold text-brand-deep mb-1">Net Monthly In-Hand Salary</label>
        <input 
          type="text" 
          :value="profile.income" 
          @input="update('income', $event.target.value)"
          placeholder="e.g. Rs. 75,000 / month" 
          class="w-full bg-surface-canvas border border-surface-border rounded-lg px-3 py-2 text-xs text-brand-deep placeholder-brand-muted/60 focus:outline-none focus:border-brand"
        />
      </div>

      <!-- Requested Loan Amount -->
      <div>
        <label class="block font-semibold text-brand-deep mb-1">Target Loan Quantum</label>
        <input 
          type="text" 
          :value="profile.requested_amount" 
          @input="update('requested_amount', $event.target.value)"
          placeholder="e.g. Rs. 35 Lakhs" 
          class="w-full bg-surface-canvas border border-surface-border rounded-lg px-3 py-2 text-xs text-brand-deep placeholder-brand-muted/60 focus:outline-none focus:border-brand"
        />
      </div>
    </div>

    <!-- Footer Action -->
    <div class="p-3 border-t border-surface-border bg-surface-canvas flex gap-2">
      <button 
        @click="$emit('reset')" 
        class="flex-1 py-2 text-xs font-semibold text-brand-muted hover:text-brand-deep hover:bg-surface-secondary rounded-lg border border-surface-border transition"
      >
        Reset Filters
      </button>
      <button 
        @click="$emit('close')" 
        class="flex-1 py-2 text-xs font-semibold bg-brand hover:bg-brand-hover text-white rounded-lg shadow-sm transition"
      >
        Apply to Advisor
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { SlidersHorizontal, X } from 'lucide-vue-next'

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  },
  profile: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['close', 'update-profile', 'reset'])

const update = (key, value) => {
  emit('update-profile', { ...props.profile, [key]: value })
}

const scoreColor = computed(() => {
  const s = props.profile.cibil_score
  if (s >= 750) return 'text-sage'
  if (s >= 650) return 'text-amber-700'
  return 'text-red-700'
})
</script>

