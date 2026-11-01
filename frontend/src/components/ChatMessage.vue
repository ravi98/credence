<template>
  <div 
    class="w-full py-5 px-4 md:px-6 transition-colors border-b border-transparent"
    :class="message.role === 'assistant' ? 'bg-[#212121]' : 'bg-[#262626]/40'"
  >
    <div class="max-w-3xl mx-auto flex gap-4 md:gap-5 items-start">
      <!-- Avatar -->
      <div class="flex-shrink-0 mt-0.5">
        <div 
          v-if="message.role === 'assistant'" 
          class="w-8 h-8 rounded-full bg-emerald-600/90 text-white flex items-center justify-center font-bold text-xs shadow-md border border-emerald-400/30"
          title="FinNav AI"
        >
          <Sparkles class="w-4 h-4 text-emerald-200" />
        </div>
        <div 
          v-else 
          class="w-8 h-8 rounded-full bg-stone-700 text-stone-200 flex items-center justify-center text-xs font-semibold shadow-sm"
          title="User"
        >
          <User class="w-4 h-4 text-stone-300" />
        </div>
      </div>

      <!-- Message Content Area -->
      <div class="flex-1 min-w-0 space-y-2.5">
        <!-- Header / Role & Intent Badge -->
        <div class="flex items-center justify-between gap-2">
          <div class="flex items-center gap-2 flex-wrap">
            <span class="font-semibold text-sm text-gray-200">
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
          <div v-if="message.role === 'assistant' && !message.loading" class="flex items-center gap-1 opacity-70 hover:opacity-100 transition">
            <button 
              @click="copyText" 
              class="p-1 text-gray-400 hover:text-white rounded hover:bg-white/10 transition text-xs flex items-center gap-1"
              :title="copied ? 'Copied!' : 'Copy response'"
            >
              <Check v-if="copied" class="w-3.5 h-3.5 text-emerald-400" />
              <Copy v-else class="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        <!-- Loading Skeleton -->
        <div v-if="message.loading" class="space-y-2 py-2">
          <div class="flex items-center gap-2 text-xs text-emerald-400 font-mono">
            <Loader2 class="w-3.5 h-3.5 animate-spin" />
            <span>Consulting LangGraph engine & ChromaDB catalog...</span>
          </div>
          <div class="h-3.5 bg-white/10 rounded w-3/4 animate-pulse"></div>
          <div class="h-3.5 bg-white/10 rounded w-1/2 animate-pulse"></div>
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
          class="mt-4 pt-3 border-t border-white/10"
        >
          <button 
            @click="sourcesOpen = !sourcesOpen"
            class="flex items-center gap-2 text-xs font-medium text-emerald-400 hover:text-emerald-300 transition py-1"
          >
            <ShieldCheck class="w-4 h-4 text-emerald-400" />
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
  ChevronDown 
} from 'lucide-vue-next'
import SourceCard from './SourceCard.vue'

const props = defineProps({
  message: {
    type: Object,
    required: true
  }
})

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

const badgeInfo = computed(() => {
  const intent = props.message.intent
  if (!intent) return null

  const isRec = intent === 'RECOMMENDATION'
  const hasCandidates = props.message.candidates && props.message.candidates.length > 0

  if (isRec && !hasCandidates) {
    return {
      label: 'Eligibility Advisory',
      icon: '⚠️',
      colorClass: 'bg-amber-500/10 text-amber-300 border-amber-500/30'
    }
  }

  const map = {
    'COMPARISON': {
      label: 'Scheme Comparison',
      icon: '⚖️',
      colorClass: 'bg-indigo-500/10 text-indigo-300 border-indigo-500/30'
    },
    'RECOMMENDATION': {
      label: 'Personalized Recommendation',
      icon: '🔍',
      colorClass: 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'
    },
    'CONCEPT_FAQ': {
      label: 'Banking Concept & Regulation',
      icon: '📚',
      colorClass: 'bg-blue-500/10 text-blue-300 border-blue-500/30'
    },
    'ELIGIBILITY_QUERY': {
      label: 'Eligibility & Criteria',
      icon: '📋',
      colorClass: 'bg-purple-500/10 text-purple-300 border-purple-500/30'
    },
    'META_CHAT': {
      label: 'Clarification',
      icon: '💬',
      colorClass: 'bg-gray-500/10 text-gray-300 border-gray-500/30'
    },
    'EMI_CALCULATOR': {
      label: 'Exact EMI Calculation',
      icon: '🧮',
      colorClass: 'bg-teal-500/10 text-teal-300 border-teal-500/30'
    }
  }

  return map[intent] || {
    label: intent,
    icon: '⚡',
    colorClass: 'bg-stone-500/10 text-stone-300 border-stone-500/30'
  }
})
</script>

