<template>
  <div class="border border-surface-border rounded-lg p-3 bg-white hover:border-brand/40 transition text-sm shadow-sm">
    <div class="flex items-start justify-between gap-2 mb-1.5">
      <div>
        <h4 class="font-semibold text-brand-deep flex items-center gap-1.5 text-xs sm:text-sm">
          <span>{{ candidate.metadata?.scheme_name || 'Verified Bank Scheme' }}</span>
        </h4>
        <p class="text-xs text-brand-muted">
          {{ candidate.metadata?.institution }} 
          <span v-if="candidate.metadata?.sector" class="text-brand-muted/70">· {{ candidate.metadata.sector }}</span>
        </p>
      </div>
      <a 
        v-if="candidate.metadata?.source_url" 
        :href="candidate.metadata.source_url" 
        target="_blank" 
        rel="noopener noreferrer"
        class="text-xs text-brand hover:text-brand-hover flex items-center gap-1 bg-surface-light px-2 py-1 rounded border border-brand/20 whitespace-nowrap transition font-medium"
      >
        <span>Portal</span>
        <ExternalLink class="w-3 h-3" />
      </a>
    </div>

    <div class="grid grid-cols-2 gap-2 mt-2 pt-2 border-t border-surface-border text-xs text-brand-deep">
      <div>
        <span class="text-brand-muted block text-[11px]">Interest Rate:</span>
        <span class="font-semibold font-tabular text-brand-deep">{{ candidate.metadata?.interest_rate_range || 'Subject to risk' }}</span>
      </div>
      <div>
        <span class="text-brand-muted block text-[11px]">Benchmark:</span>
        <span class="font-medium">{{ candidate.metadata?.benchmark || 'EBLR / MCLR' }}</span>
      </div>
    </div>

    <div v-if="candidate.metadata?.compact_key" class="mt-2 text-[10px] font-mono text-brand-muted truncate bg-surface-secondary px-2 py-0.5 rounded">
      Key: {{ candidate.metadata.compact_key }}
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
