<template>
  <div 
    class="w-full py-5 px-4 md:px-6 transition-colors border-b border-surface-border/60"
    :class="message.role === 'assistant' ? 'bg-surface-canvas' : 'bg-surface-secondary/40'"
  >
    <div class="max-w-3xl mx-auto flex gap-3 sm:gap-4 items-start">
      <!-- Avatar -->
      <div class="flex-shrink-0 mt-0.5">
        <div 
          v-if="message.role === 'assistant'" 
          class="w-8 h-8 rounded-lg bg-brand text-white flex items-center justify-center font-bold text-xs shadow-sm border border-brand/20"
          title="FinNav AI Advisor"
        >
          <Sparkles class="w-4 h-4 text-sage-light" />
        </div>
        <div 
          v-else 
          class="w-8 h-8 rounded-lg bg-brand-deep text-white flex items-center justify-center text-xs font-semibold shadow-sm"
          title="User"
        >
          <User class="w-4 h-4 text-surface-secondary" />
        </div>
      </div>

      <!-- Message Content Area -->
      <div class="flex-1 min-w-0 space-y-2.5">
        <!-- Header / Role & Intent Badge -->
        <div class="flex items-center justify-between gap-2">
          <div class="flex items-center gap-2 flex-wrap">
            <span class="font-bold text-sm text-brand-deep">
              {{ message.role === 'assistant' ? 'FinNav Advisor' : 'You' }}
            </span>

            <!-- Intent Badge -->
            <span 
              v-if="message.role === 'assistant' && badgeInfo" 
              class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium border"
              :class="badgeInfo.colorClass"
            >
              <span>{{ badgeInfo.icon }}</span>
              <span>{{ badgeInfo.label }}</span>
            </span>
          </div>

          <!-- Actions -->
          <div v-if="message.role === 'assistant' && !message.loading" class="flex items-center gap-1">
            <button 
              @click="copyText" 
              class="p-1.5 text-brand-muted hover:text-brand-deep rounded hover:bg-surface-secondary transition text-xs flex items-center gap-1"
              :title="copied ? 'Copied!' : 'Copy response'"
            >
              <Check v-if="copied" class="w-3.5 h-3.5 text-sage" />
              <Copy v-else class="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        <!-- Loading Skeleton -->
        <div v-if="message.loading" class="space-y-2 py-2">
          <div class="flex items-center gap-2 text-xs text-brand font-medium">
            <Loader2 class="w-3.5 h-3.5 animate-spin" />
            <span>Consulting LangGraph engine & 163 verified bank schemes...</span>
          </div>
          <div class="h-3.5 bg-surface-secondary rounded w-3/4 animate-pulse"></div>
          <div class="h-3.5 bg-surface-secondary rounded w-1/2 animate-pulse"></div>
        </div>

        <!-- Rendered Text -->
        <div 
          v-else 
          class="markdown-body text-sm leading-relaxed" 
          v-html="renderedContent"
        ></div>

        <!-- Verified Source Fact Checks (ChromaDB Grounding) -->
        <div 
          v-if="message.role === 'assistant' && message.candidates && message.candidates.length > 0" 
          class="mt-4 pt-3 border-t border-surface-border"
        >
          <button 
            @click="sourcesOpen = !sourcesOpen"
            class="flex items-center gap-2 text-xs font-semibold text-brand hover:text-brand-hover transition py-1"
          >
            <ShieldCheck class="w-4 h-4 text-sage" />
            <span>Grounded Fact Check: {{ message.candidates.length }} Official Bank Schemes</span>
            <ChevronDown 
              class="w-3.5 h-3.5 transition-transform duration-200" 
              :class="{ 'rotate-180': sourcesOpen }" 
            />
          </button>

          <div v-show="sourcesOpen" class="mt-2.5 grid grid-cols-1 md:grid-cols-2 gap-2.5">
            <SourceCard 
              v-for="(cand, idx) in message.candidates" 
              :key="idx" 
              :candidate="cand" 
            />
          </div>
        </div>

        <!-- Contextual Follow-up Suggestions -->
        <div 
          v-if="message.role === 'assistant' && !message.loading && contextualSuggestions.length > 0"
          class="mt-3 pt-2.5 flex items-center gap-1.5 flex-wrap"
        >
          <span class="text-xs text-brand-muted font-medium flex items-center gap-1">
            <CornerDownRight class="w-3 h-3" />
            Suggested:
          </span>
          <button
            v-for="(sug, idx) in contextualSuggestions"
            :key="idx"
            @click="$emit('select-suggestion', sug)"
            class="text-xs bg-white hover:bg-surface-light text-brand border border-surface-border hover:border-brand/30 px-2.5 py-1 rounded-full transition shadow-2xs font-medium"
          >
            {{ sug }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { 
  Sparkles, 
  User, 
  Copy, 
  Check, 
  Loader2, 
  ShieldCheck, 
  ChevronDown,
  CornerDownRight
} from 'lucide-vue-next'
import SourceCard from './SourceCard.vue'

const props = defineProps({
  message: {
    type: Object,
    required: true
  }
})

defineEmits(['select-suggestion'])

const copied = ref(false)
const sourcesOpen = ref(false)

const copyText = async () => {
  if (!props.message.content) return
  await navigator.clipboard.writeText(props.message.content)
  copied.value = true
  setTimeout(() => {
    copied.value = false
  }, 2000)
}

const renderedContent = computed(() => {
  if (!props.message.content) return ''
  const rawHtml = marked.parse(props.message.content)
  return DOMPurify.sanitize(rawHtml)
})

const contextualSuggestions = computed(() => {
  const intent = props.message.intent
  if (!intent) return []

  if (intent === 'COMPARISON') {
    return [
      "What are the processing charges?",
      "Compare with ICICI Bank",
      "Calculate EMI for 20 years"
    ]
  } else if (intent === 'EMI_CALCULATOR') {
    return [
      "Compare actual bank interest rates for this amount",
      "What if I increase tenure by 5 years?",
      "How to reduce total interest payment?"
    ]
  } else if (intent === 'CONCEPT_FAQ') {
    return [
      "Show floating-rate schemes under EBLR",
      "Which bank currently offers the lowest spread?",
      "What documents are needed for approval?"
    ]
  } else if (intent === 'ELIGIBILITY_QUERY') {
    return [
      "How to improve my loan eligibility?",
      "Can I add a co-applicant to increase quantum?",
      "Explore schemes for salaried professionals"
    ]
  }
  
  return [
    "Compare top 3 banks side-by-side",
    "Calculate my monthly EMI",
    "What are the prepayment charges?"
  ]
})

const badgeInfo = computed(() => {
  const intent = props.message.intent
  if (!intent) return null

  const isRec = intent === 'RECOMMENDATION'
  const hasCandidates = props.message.candidates && props.message.candidates.length > 0

  if (isRec && !hasCandidates) {
    return {
      label: 'Eligibility Advisory',
      icon: '⚠️',
      colorClass: 'bg-amber-50 text-amber-800 border-amber-200'
    }
  }

  const map = {
    'COMPARISON': {
      label: 'Scheme Comparison',
      icon: '⚖️',
      colorClass: 'bg-indigo-50 text-indigo-800 border-indigo-200'
    },
    'RECOMMENDATION': {
      label: 'Personalized Recommendation',
      icon: '🔍',
      colorClass: 'bg-surface-light text-brand border-brand/20'
    },
    'CONCEPT_FAQ': {
      label: 'Banking Regulation & Facts',
      icon: '📚',
      colorClass: 'bg-blue-50 text-blue-800 border-blue-200'
    },
    'ELIGIBILITY_QUERY': {
      label: 'Eligibility & Criteria',
      icon: '📋',
      colorClass: 'bg-purple-50 text-purple-800 border-purple-200'
    },
    'META_CHAT': {
      label: 'Clarification',
      icon: '💬',
      colorClass: 'bg-surface-secondary text-brand-deep border-surface-border'
    },
    'EMI_CALCULATOR': {
      label: 'Exact EMI Calculation',
      icon: '🧮',
      colorClass: 'bg-teal-50 text-teal-800 border-teal-200'
    }
  }

  return map[intent] || {
    label: intent,
    icon: '⚡',
    colorClass: 'bg-surface-secondary text-brand-muted border-surface-border'
  }
})
</script>
