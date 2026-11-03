<template>
  <div class="mt-4 rounded-2xl border border-brand/20 bg-gradient-to-br from-surface-light/80 via-white to-surface-secondary/30 p-4 sm:p-5 shadow-2xs space-y-4">
    <!-- Header with Educational Banner -->
    <div class="flex items-start gap-3 border-b border-surface-border/80 pb-3">
      <div class="w-8 h-8 rounded-lg bg-brand/10 text-brand flex items-center justify-center flex-shrink-0 mt-0.5">
        <HelpCircle class="w-4.5 h-4.5" />
      </div>
      <div class="min-w-0 flex-1">
        <div class="flex items-center gap-2 flex-wrap">
          <span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-brand/10 text-brand border border-brand/20">
            {{ clarification?.category || 'Loan' }} Discovery
          </span>
          <span class="text-xs font-semibold text-brand-muted">
            Zero Guesswork · RBI Underwriting Standards
          </span>
        </div>
        <p class="text-xs text-brand-deep/80 mt-1 leading-relaxed">
          {{ clarification?.educational_summary || 'To recommend genuine, verified loan matches without risking rejection, please clarify these key details.' }}
        </p>
      </div>
    </div>

    <!-- Questions, Direct Inputs & Interactive Chips -->
    <div class="space-y-4">
      <div 
        v-for="(q, qIdx) in questions" 
        :key="q.id || qIdx"
        class="bg-white rounded-xl p-3.5 border transition shadow-2xs space-y-2.5"
        :class="selectedAnswers[q.id] ? 'border-brand/40 ring-1 ring-brand/10' : 'border-surface-border'"
      >
        <!-- Question Title & Selection Status Badge -->
        <div class="flex items-center justify-between gap-2">
          <div class="flex items-center gap-2">
            <span class="w-5 h-5 rounded-full bg-brand-deep text-white text-[11px] font-bold flex items-center justify-center flex-shrink-0">
              {{ qIdx + 1 }}
            </span>
            <h4 class="text-xs sm:text-sm font-bold text-brand-deep">
              {{ q.question }}
            </h4>
          </div>

          <span 
            v-if="selectedAnswers[q.id]" 
            class="text-[11px] font-bold text-sage bg-sage/10 px-2 py-0.5 rounded-md flex items-center gap-1 border border-sage/20 flex-shrink-0"
          >
            <Check class="w-3 h-3" /> Selected
          </span>
        </div>

        <!-- Educational Why-It-Matters Callout -->
        <div v-if="q.explanation" class="text-[11px] text-brand-muted bg-surface-canvas rounded-lg px-2.5 py-1.5 flex items-start gap-1.5 border border-surface-border/60">
          <Info class="w-3.5 h-3.5 text-sage flex-shrink-0 mt-0.5" />
          <span class="leading-normal"><strong class="text-brand font-semibold">Why this matters:</strong> {{ q.explanation }}</span>
        </div>

        <!-- Direct Input Box (If input_type is currency, text, or number) -->
        <div v-if="q.input_type && q.input_type !== 'select'" class="pt-1">
          <div class="relative rounded-xl border bg-surface-canvas flex items-center px-3 py-2 border-surface-border focus-within:border-brand/60 focus-within:ring-2 focus-within:ring-brand/10 transition shadow-2xs">
            <span v-if="q.input_type === 'currency'" class="text-brand font-bold text-sm mr-2 select-none">₹</span>
            <input
              :type="q.input_type === 'number' ? 'number' : 'text'"
              v-model="inputValues[q.id]"
              @input="handleCustomInput(q)"
              :placeholder="q.placeholder || (q.input_type === 'currency' ? 'Enter amount (e.g. 85,00,000)' : 'Type answer...')"
              class="w-full bg-transparent border-0 text-brand-deep placeholder-brand-muted/50 text-xs sm:text-sm focus:outline-none font-medium"
            />
          </div>
        </div>

        <!-- Option Chips (If available) -->
        <div v-if="q.options && q.options.length > 0" class="space-y-1.5 pt-1">
          <div v-if="q.input_type && q.input_type !== 'select'" class="text-[11px] font-semibold text-brand-muted">
            Or quick select:
          </div>
          <div class="flex items-center gap-2 flex-wrap">
            <button
              v-for="(opt, optIdx) in q.options"
              :key="optIdx"
              @click="handleOptionClick(q, opt)"
              class="text-xs font-semibold px-3 py-1.5 rounded-lg border transition shadow-2xs flex items-center gap-1.5 cursor-pointer select-none"
              :class="selectedAnswers[q.id]?.label === opt.label
                ? 'bg-brand text-white border-brand shadow-sm ring-2 ring-brand/20'
                : 'bg-surface-secondary/70 hover:bg-surface-secondary text-brand-deep border-surface-border hover:border-brand/40'"
            >
              <span>{{ opt.label }}</span>
              <Check v-if="selectedAnswers[q.id]?.label === opt.label" class="w-3 h-3 text-white" />
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Action Confirmation / Submission Dock -->
    <div 
      class="pt-3 border-t border-surface-border/80 flex items-center justify-between gap-3 flex-wrap"
    >
      <div class="text-xs font-semibold text-brand-muted flex items-center gap-1.5">
        <Sparkles class="w-3.5 h-3.5 text-brand" />
        <span>{{ selectedCount }} of {{ questions.length }} parameters filled</span>
      </div>

      <button
        @click="submitAllSelected"
        :disabled="selectedCount === 0"
        class="px-4 py-2 rounded-xl text-xs sm:text-sm font-bold flex items-center gap-2 transition shadow-sm cursor-pointer"
        :class="selectedCount > 0 
          ? 'bg-brand text-white hover:bg-brand-hover shadow-md cursor-pointer' 
          : 'bg-surface-secondary text-brand-muted/50 cursor-not-allowed'"
      >
        <span>{{ submitButtonLabel }}</span>
        <ArrowRight class="w-4 h-4" />
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { HelpCircle, Info, Check, Sparkles, ArrowRight } from 'lucide-vue-next'

const props = defineProps({
  clarification: {
    type: Object,
    default: () => null
  }
})

const emit = defineEmits(['select-option'])

const questions = computed(() => {
  return props.clarification?.next_questions || []
})

// Stores selected option or input per question ID: { [qId]: { label, value, field } }
const selectedAnswers = ref({})

// Stores text / number values for direct input boxes
const inputValues = ref({})

const selectedCount = computed(() => {
  return Object.keys(selectedAnswers.value).length
})

const submitButtonLabel = computed(() => {
  const isLtv = (props.clarification?.category || '').toLowerCase().includes('ltv')
  if (selectedCount.value === questions.value.length) {
    return isLtv ? 'Check 90% LTV Sanction' : 'Find Verified Loan Matches'
  }
  return `Submit Details (${selectedCount.value})`
})

const handleOptionClick = (question, option) => {
  selectedAnswers.value[question.id] = {
    label: option.label,
    value: option.value,
    field: question.field
  }
  // Sync direct input box with option label
  if (question.input_type && question.input_type !== 'select') {
    inputValues.value[question.id] = option.label
  }

  // If only 1 question was asked, auto submit immediately
  if (questions.value.length === 1) {
    submitAllSelected()
  }
}

const handleCustomInput = (question) => {
  const val = (inputValues.value[question.id] || '').trim()
  if (val.length > 0) {
    selectedAnswers.value[question.id] = {
      label: val,
      value: val,
      field: question.field,
      custom: true
    }
  } else {
    delete selectedAnswers.value[question.id]
  }
}

const submitAllSelected = () => {
  const parts = []
  const category = props.clarification?.category || 'Loan'

  for (const q of questions.value) {
    const sel = selectedAnswers.value[q.id]
    if (sel) {
      const label = sel.label
      if (q.field === 'requested_amount') {
        parts.push(`loan amount of ${label}`)
      } else if (q.field === 'property_value') {
        parts.push(`property value of ${label}`)
      } else if (q.field === 'property_type') {
        parts.push(`property type: ${label}`)
      } else if (q.field === 'city') {
        parts.push(`located in ${label}`)
      } else if (q.field === 'preferred_tenure_months') {
        parts.push(`tenure of ${label}`)
      } else if (q.field === 'monthly_net_income') {
        parts.push(`monthly income of ${label}`)
      } else if (q.field === 'existing_monthly_emi') {
        parts.push(`existing monthly EMIs: ${label}`)
      } else if (q.field === 'employment_type') {
        parts.push(`employment: ${label}`)
      } else if (q.field === 'self_reported_credit_score') {
        parts.push(`credit score: ${label}`)
      } else if (q.field === 'priorities') {
        parts.push(`priority: ${label}`)
      } else {
        parts.push(`${q.question}: ${label}`)
      }
    }
  }

  if (parts.length > 0) {
    const summaryText = `Looking for ${category} with ${parts.join(', ')}.`
    emit('select-option', summaryText)
  }
}
</script>
