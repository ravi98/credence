<template>
  <div class="min-h-screen flex flex-col bg-surface-canvas text-brand-deep">
    <Navbar />

    <main class="flex-1 max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10 w-full">
      <!-- Header -->
      <div class="max-w-3xl mb-8">
        <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-surface-secondary border border-surface-border text-xs font-semibold text-brand mb-3">
          <Calculator class="w-3.5 h-3.5" />
          <span>Deterministic Repayment Engine</span>
        </div>
        <h1 class="text-3xl font-bold font-serif text-brand-deep mb-2">
          Loan EMI Calculator
        </h1>
        <p class="text-sm text-brand-muted">
          Calculate your monthly installment, cumulative interest payout, and principal amortization according to standard Indian banking formulas.
        </p>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        <!-- Controls Left (7 cols) -->
        <div class="lg:col-span-7 bg-white p-6 rounded-2xl border border-surface-border shadow-xs space-y-6">
          <!-- Loan Amount -->
          <div>
            <div class="flex justify-between items-center mb-1.5">
              <label class="text-xs font-semibold text-brand-deep">Loan Quantum</label>
              <span class="text-base font-bold font-tabular text-brand">₹ {{ formattedAmount }}</span>
            </div>
            <input 
              type="range" 
              min="100000" 
              max="20000000" 
              step="50000"
              v-model.number="amount"
              @input="recalculate"
              class="w-full accent-brand bg-surface-secondary h-2 rounded-lg appearance-none cursor-pointer"
            />
            <div class="flex justify-between text-[11px] text-brand-muted mt-1.5 flex-wrap gap-1">
              <button @click="setAmount(1000000)" class="hover:text-brand">₹10 Lakhs</button>
              <button @click="setAmount(2500000)" class="hover:text-brand">₹25 Lakhs</button>
              <button @click="setAmount(5000000)" class="hover:text-brand">₹50 Lakhs</button>
              <button @click="setAmount(10000000)" class="hover:text-brand">₹1 Crore</button>
            </div>
          </div>

          <!-- Interest Rate -->
          <div>
            <div class="flex justify-between items-center mb-1.5">
              <label class="text-xs font-semibold text-brand-deep">Annual Interest Rate (% p.a.)</label>
              <span class="text-base font-bold font-tabular text-brand">{{ rate }}%</span>
            </div>
            <input 
              type="range" 
              min="6.5" 
              max="18.0" 
              step="0.05"
              v-model.number="rate"
              @input="recalculate"
              class="w-full accent-brand bg-surface-secondary h-2 rounded-lg appearance-none cursor-pointer"
            />
            <div class="flex justify-between text-[11px] text-brand-muted mt-1.5">
              <span>6.5% (Prime Home)</span>
              <span>8.75% (Standard)</span>
              <span>18.0% (Personal/NBFC)</span>
            </div>
          </div>

          <!-- Tenure -->
          <div>
            <div class="flex justify-between items-center mb-1.5">
              <label class="text-xs font-semibold text-brand-deep">Tenure (Years)</label>
              <span class="text-base font-bold font-tabular text-brand">{{ tenureYears }} Years ({{ tenureYears * 12 }} Months)</span>
            </div>
            <input 
              type="range" 
              min="1" 
              max="30" 
              step="1"
              v-model.number="tenureYears"
              @input="recalculate"
              class="w-full accent-brand bg-surface-secondary h-2 rounded-lg appearance-none cursor-pointer"
            />
            <div class="flex justify-between text-[11px] text-brand-muted mt-1.5">
              <span>5 Years (Auto)</span>
              <span>15 Years</span>
              <span>30 Years (Home)</span>
            </div>
          </div>
        </div>

        <!-- Result Card Right (5 cols) -->
        <div class="lg:col-span-5 bg-white p-6 rounded-2xl border border-surface-border shadow-md space-y-6">
          <div class="text-center p-5 rounded-xl bg-surface-canvas border border-surface-border">
            <span class="text-xs font-semibold uppercase tracking-wider text-brand-muted block mb-1">
              Monthly Repayment (EMI)
            </span>
            <div class="text-3xl sm:text-4xl font-bold font-tabular text-brand-deep">
              ₹ {{ formatNumber(result.monthly_emi) }}
            </div>
            <span class="text-[11px] text-brand-muted mt-1 block">
              For {{ tenureYears * 12 }} installments
            </span>
          </div>

          <!-- Breakdown Metrics -->
          <div class="space-y-3 text-xs">
            <div class="flex justify-between py-2 border-b border-surface-border">
              <span class="text-brand-muted">Principal Amount:</span>
              <span class="font-bold font-tabular text-brand-deep">₹ {{ formatNumber(amount) }}</span>
            </div>
            <div class="flex justify-between py-2 border-b border-surface-border">
              <span class="text-brand-muted">Total Interest Payable:</span>
              <span class="font-bold font-tabular text-brand">₹ {{ formatNumber(result.total_interest) }}</span>
            </div>
            <div class="flex justify-between py-2 border-b border-surface-border">
              <span class="text-brand-muted">Total Payment (P + I):</span>
              <span class="font-bold font-tabular text-brand-deep">₹ {{ formatNumber(result.total_payment) }}</span>
            </div>
          </div>

          <!-- Visual Bar -->
          <div>
            <div class="flex justify-between text-[11px] text-brand-muted mb-1.5">
              <span>Principal: {{ (100 - result.interest_ratio_percent).toFixed(1) }}%</span>
              <span>Interest: {{ result.interest_ratio_percent }}%</span>
            </div>
            <div class="w-full h-3 rounded-full bg-surface-secondary overflow-hidden flex">
              <div 
                class="bg-brand h-full transition-all duration-300" 
                :style="{ width: `${100 - result.interest_ratio_percent}%` }"
              ></div>
              <div 
                class="bg-amber-600 h-full transition-all duration-300" 
                :style="{ width: `${result.interest_ratio_percent}%` }"
              ></div>
            </div>
          </div>

          <!-- Next Step Action -->
          <div class="pt-2">
            <button 
              @click="compareForAmount"
              class="w-full bg-brand hover:bg-brand-hover text-white text-xs font-semibold py-3 rounded-xl transition shadow-sm flex items-center justify-center gap-2"
            >
              <Sparkles class="w-4 h-4 text-sage-light" />
              <span>Ask Credence to Compare Schemes for This Quantum</span>
            </button>
          </div>
        </div>
      </div>
    </main>

    <Footer />
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Calculator, Sparkles } from 'lucide-vue-next'
import Navbar from '../components/Navbar.vue'
import Footer from '../components/Footer.vue'

const router = useRouter()

const amount = ref(2500000)
const rate = ref(8.65)
const tenureYears = ref(20)

const result = reactive({
  monthly_emi: 21929,
  total_interest: 2762960,
  total_payment: 5262960,
  interest_ratio_percent: 52.5
})

const formatNumber = (num) => {
  if (!num) return '0'
  return Math.round(num).toLocaleString('en-IN')
}

const formattedAmount = computed(() => {
  return formatNumber(amount.value)
})

const setAmount = (val) => {
  amount.value = val
  recalculate()
}

const recalculate = () => {
  const P = amount.value
  const annual_rate = rate.value
  const years = tenureYears.value
  const n = years * 12
  const r = (annual_rate / 100) / 12

  let emi = 0
  if (r === 0) {
    emi = P / n
  } else {
    emi = (P * r * Math.pow(1 + r, n)) / (Math.pow(1 + r, n) - 1)
  }

  const total_payment = emi * n
  const total_interest = total_payment - P

  result.monthly_emi = Math.round(emi)
  result.total_payment = Math.round(total_payment)
  result.total_interest = Math.round(total_interest)
  result.interest_ratio_percent = total_payment > 0 ? parseFloat(((total_interest / total_payment) * 100).toFixed(1)) : 0
}

const compareForAmount = () => {
  const lakhs = (amount.value / 100000).toFixed(1).replace('.0', '')
  router.push({
    path: '/advisor',
    query: {
      q: `I need a loan of ₹${lakhs} Lakhs for ${tenureYears.value} years. Which bank offers the lowest EMI and processing fee?`
    }
  })
}

onMounted(() => {
  recalculate()
})
</script>

