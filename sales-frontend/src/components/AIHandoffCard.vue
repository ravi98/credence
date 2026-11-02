<template>
  <div class="rounded-3xl border border-brand/20 bg-gradient-to-br from-surface-light via-white to-surface-secondary/30 p-5 sm:p-6 shadow-xs space-y-6">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-brand/15">
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-2xl bg-brand text-white flex items-center justify-center shadow-xs">
          <Sparkles class="w-5 h-5 text-sage-light" />
        </div>
        <div>
          <div class="flex items-center gap-2">
            <h3 class="font-extrabold text-base sm:text-lg text-brand-deep leading-tight">
              AI Underwriting Handoff Briefing
            </h3>
            <span class="px-2 py-0.5 rounded-full text-[10px] font-extrabold bg-sage/10 text-sage border border-sage/20 uppercase tracking-wider">
              Frozen Artifact
            </span>
          </div>
          <p class="text-xs text-brand-muted font-medium mt-0.5">
            Generated at submission · Zero runtime LLM latency
          </p>
        </div>
      </div>

      <!-- Generated At Timestamp -->
      <div v-if="summary?.generated_at" class="text-right text-[11px] text-brand-muted font-mono">
        Generated: {{ formatDate(summary.generated_at) }}
      </div>
    </div>

    <!-- Executive Summary -->
    <div v-if="summary?.executive_summary" class="p-4 rounded-2xl bg-white border border-surface-border space-y-1.5">
      <span class="text-[10px] uppercase font-bold tracking-wider text-brand-muted block">
        Executive Underwriting Verdict
      </span>
      <p class="text-sm font-medium text-brand-deep leading-relaxed">
        {{ summary.executive_summary }}
      </p>
    </div>

    <!-- 2 Column Strengths vs Risks Grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <!-- Borrower Strengths -->
      <div class="p-4 rounded-2xl bg-sage/5 border border-sage/20 space-y-2.5">
        <div class="flex items-center gap-2 text-sage">
          <CheckCircle2 class="w-4 h-4 flex-shrink-0" />
          <h4 class="text-xs font-bold uppercase tracking-wider">Key Underwriting Strengths</h4>
        </div>
        <ul class="space-y-2 text-xs text-brand-deep">
          <li 
            v-for="(st, idx) in summary?.borrower_strengths || []" 
            :key="idx"
            class="flex items-start gap-2 leading-relaxed"
          >
            <span class="text-sage font-bold">•</span>
            <span>{{ st }}</span>
          </li>
        </ul>
      </div>

      <!-- Risk Factors & Mitigants -->
      <div class="p-4 rounded-2xl bg-amber-50/60 border border-amber-200/80 space-y-2.5">
        <div class="flex items-center gap-2 text-amber-800">
          <AlertTriangle class="w-4 h-4 flex-shrink-0" />
          <h4 class="text-xs font-bold uppercase tracking-wider">Risk Factors & Mitigants</h4>
        </div>
        <ul class="space-y-2 text-xs text-brand-deep">
          <li 
            v-for="(rf, idx) in summary?.risk_factors_and_mitigants || []" 
            :key="idx"
            class="flex items-start gap-2 leading-relaxed"
          >
            <span class="text-amber-700 font-bold">•</span>
            <span>{{ rf }}</span>
          </li>
        </ul>
      </div>
    </div>

    <!-- Recommended Lender Pitch Points -->
    <div v-if="summary?.recommended_lender_pitch?.length > 0" class="space-y-2">
      <div class="flex items-center gap-2 text-brand">
        <Target class="w-4 h-4" />
        <h4 class="text-xs font-bold uppercase tracking-wider">Recommended Sales & Lender Positioning</h4>
      </div>
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
        <div 
          v-for="(pt, idx) in summary.recommended_lender_pitch" 
          :key="idx"
          class="p-3 rounded-xl bg-white border border-surface-border text-xs text-brand-deep font-medium flex items-start gap-2"
        >
          <span class="w-4 h-4 rounded-full bg-brand/10 text-brand flex items-center justify-center font-bold text-[10px] flex-shrink-0 mt-0.5">{{ idx + 1 }}</span>
          <span>{{ pt }}</span>
        </div>
      </div>
    </div>

    <!-- Actionable Checklist for Sales Officer -->
    <div v-if="summary?.recommended_next_steps?.length > 0" class="space-y-2 pt-2">
      <div class="flex items-center gap-2 text-brand-deep">
        <ListTodo class="w-4 h-4 text-brand" />
        <h4 class="text-xs font-bold uppercase tracking-wider">Underwriting Next Steps Checklist</h4>
      </div>
      <div class="space-y-1.5">
        <div 
          v-for="(ns, idx) in summary.recommended_next_steps" 
          :key="idx"
          class="p-3 rounded-xl bg-white border border-surface-border text-xs text-brand-deep font-medium flex items-center gap-3"
        >
          <input type="checkbox" class="rounded text-brand focus:ring-brand" />
          <span>{{ ns }}</span>
        </div>
      </div>
    </div>

    <!-- Documentation Checklist -->
    <div v-if="summary?.recommended_documents?.length > 0" class="space-y-2 pt-2 border-t border-brand/15">
      <div class="flex items-center gap-2 text-brand-muted">
        <FileCheck class="w-4 h-4" />
        <h4 class="text-xs font-bold uppercase tracking-wider">Required Document Dossier</h4>
      </div>
      <div class="flex flex-wrap gap-2">
        <span 
          v-for="(doc, idx) in summary.recommended_documents" 
          :key="idx"
          class="px-3 py-1 rounded-lg bg-surface-secondary text-brand-deep text-xs font-semibold border border-surface-border"
        >
          {{ doc }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { 
  Sparkles, 
  CheckCircle2, 
  AlertTriangle, 
  Target, 
  ListTodo, 
  FileCheck 
} from 'lucide-vue-next'

const props = defineProps({
  summary: {
    type: Object,
    default: () => ({})
  }
})

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  try {
    const d = new Date(dateStr)
    return d.toLocaleString('en-IN', { 
      day: 'numeric', 
      month: 'short', 
      year: 'numeric', 
      hour: '2-digit', 
      minute: '2-digit' 
    })
  } catch (e) {
    return dateStr
  }
}
</script>

