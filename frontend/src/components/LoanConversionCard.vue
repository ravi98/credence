<template>
  <div class="mt-4 rounded-2xl border-2 border-brand/20 bg-gradient-to-br from-surface-light via-white to-surface-secondary/40 p-4 sm:p-5 shadow-sm transition hover:border-brand/40">
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <!-- Left Info -->
      <div class="space-y-2 min-w-0 flex-1">
        <div class="flex items-center gap-2 flex-wrap">
          <span class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-bold bg-sage/10 text-sage border border-sage/20">
            <ShieldCheck class="w-3.5 h-3.5" />
            Credence Assisted
          </span>
          <span class="text-xs font-semibold text-brand-muted">
            Zero Advisory Fee · End-to-End Coordination
          </span>
        </div>

        <div class="min-w-0">
          <h4 class="text-base sm:text-lg font-bold text-brand-deep leading-snug truncate">
            {{ primaryCandidate?.metadata?.scheme_name || 'Verified Banking Solution' }}
          </h4>
          <p class="text-xs sm:text-sm font-semibold text-brand-muted mt-0.5">
            {{ primaryCandidate?.metadata?.institution || 'Top Banking Partners' }}
            <span v-if="primaryCandidate?.metadata?.interest_rate_range" class="text-brand font-bold">
              · {{ primaryCandidate.metadata.interest_rate_range }}
            </span>
          </p>
        </div>

        <p class="text-xs text-brand-deep/80 leading-relaxed max-w-xl">
          Get personal guidance from a verified loan specialist. We review your eligibility, collect documents at your convenience, and coordinate directly with the bank for expedited sanction.
        </p>
      </div>

      <!-- Right Action CTA -->
      <div class="flex-shrink-0 flex flex-col sm:items-end justify-center gap-2">
        <button
          @click="$emit('open-assistance', primaryCandidate)"
          class="w-full sm:w-auto px-5 py-2.5 rounded-xl bg-brand text-white font-bold text-sm shadow-md hover:bg-brand-hover transition flex items-center justify-center gap-2 group cursor-pointer"
        >
          <span>Get Help With This Loan</span>
          <ArrowRight class="w-4 h-4 transition-transform group-hover:translate-x-0.5" />
        </button>
        <span class="text-[11px] text-brand-muted text-center sm:text-right font-medium">
          No obligation · 100% confidential
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { ShieldCheck, ArrowRight } from 'lucide-vue-next'

const props = defineProps({
  candidates: {
    type: Array,
    default: () => []
  }
})

defineEmits(['open-assistance'])

const primaryCandidate = computed(() => {
  if (props.candidates && props.candidates.length > 0) {
    return props.candidates[0]
  }
  return null
})
</script>

