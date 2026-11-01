<template>
  <div class="border border-white/10 rounded-lg p-3 bg-white/[0.03] hover:bg-white/[0.06] transition text-sm">
    <div class="flex items-start justify-between gap-2 mb-1.5">
      <div>
        <h4 class="font-semibold text-white flex items-center gap-1.5">
          <span>{{ candidate.metadata?.scheme_name || 'Verified Scheme' }}</span>
        </h4>
        <p class="text-xs text-gray-400">
          {{ candidate.metadata?.institution }} 
          <span v-if="candidate.metadata?.sector" class="text-gray-500">· {{ candidate.metadata.sector }}</span>
        </p>
      </div>
      <a 
        v-if="candidate.metadata?.source_url" 
        :href="candidate.metadata.source_url" 
        target="_blank" 
        rel="noopener noreferrer"
        class="text-xs text-emerald-400 hover:text-emerald-300 flex items-center gap-1 bg-emerald-500/10 px-2 py-1 rounded border border-emerald-500/20 whitespace-nowrap transition"
      >
        <span>Portal</span>
        <ExternalLink class="w-3 h-3" />
      </a>
    </div>

    <div class="grid grid-cols-2 gap-2 mt-2 pt-2 border-t border-white/5 text-xs text-gray-300">
      <div>
        <span class="text-gray-500 block">Interest Rate:</span>
        <span class="font-medium text-emerald-300">{{ candidate.metadata?.interest_rate_range || 'Subject to risk' }}</span>
      </div>
      <div>
        <span class="text-gray-500 block">Benchmark:</span>
        <span class="font-medium">{{ candidate.metadata?.benchmark || 'EBLR / MCLR' }}</span>
      </div>
    </div>

    <div v-if="candidate.metadata?.compact_key" class="mt-2 text-[11px] font-mono text-gray-500 truncate">
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

