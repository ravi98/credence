<template>
  <div class="border border-surface-border rounded-xl p-3.5 sm:p-4 bg-white hover:border-brand/40 transition shadow-xs flex flex-col justify-between">
    <div>
      <!-- Bank Title & Portal Link -->
      <div class="flex items-start justify-between gap-2.5 mb-2.5">
        <div class="min-w-0 flex-1">
          <h4 class="font-bold text-brand-deep text-sm sm:text-base leading-snug break-words">
            {{ candidate.metadata?.scheme_name || 'Verified Bank Scheme' }}
          </h4>
          <p class="text-xs sm:text-sm text-brand-muted font-semibold mt-0.5 truncate">
            {{ candidate.metadata?.institution }} 
            <span v-if="candidate.metadata?.sector" class="text-brand-muted/70">· {{ candidate.metadata.sector }}</span>
          </p>
        </div>
        <a 
          v-if="candidate.metadata?.source_url" 
          :href="candidate.metadata.source_url" 
          target="_blank" 
          rel="noopener noreferrer"
          class="text-xs sm:text-sm text-brand hover:text-brand-hover flex items-center gap-1.5 bg-surface-light px-2.5 py-1.5 rounded-lg border border-brand/20 whitespace-nowrap transition font-bold flex-shrink-0"
        >
          <span>Portal</span>
          <ExternalLink class="w-3.5 h-3.5" />
        </a>
      </div>

      <!-- Metrics Stack with Zero Bleeding -->
      <div class="p-3 rounded-lg bg-surface-canvas border border-surface-border text-xs sm:text-sm space-y-2 mb-2">
        <div class="flex items-baseline justify-between gap-2 pb-2 border-b border-surface-border">
          <div>
            <span class="text-[10px] uppercase tracking-wider text-brand-muted block font-bold">Interest Rate</span>
            <span class="font-bold font-tabular text-brand sm:text-base leading-tight block">
              {{ candidate.metadata?.interest_rate_range || 'Subject to risk' }}
            </span>
          </div>
          <div v-if="candidate.metadata?.max_tenure_years" class="text-right">
            <span class="text-[10px] uppercase tracking-wider text-brand-muted block font-bold">Tenure</span>
            <span class="font-bold font-tabular text-brand-deep leading-tight block">
              {{ candidate.metadata.max_tenure_years }} Yrs
            </span>
          </div>
        </div>

        <div class="flex items-start justify-between gap-2">
          <span class="text-brand-muted font-medium flex-shrink-0">Benchmark:</span>
          <span class="font-semibold text-brand-deep text-right break-words min-w-0">
            {{ candidate.metadata?.benchmark || 'EBLR / MCLR' }}
          </span>
        </div>
      </div>
    </div>

    <!-- Compact Key Signature -->
    <div v-if="candidate.metadata?.compact_key" class="text-[11px] font-mono text-brand-muted truncate bg-surface-secondary px-2.5 py-1 rounded-md">
      Signature: {{ candidate.metadata.compact_key }}
    </div>
  </div>
</template>

<script setup>
import { ExternalLink } from 'lucide-vue-next'

defineProps({
  candidate: {
    type: Object,
    required: true
  }
})
</script>
