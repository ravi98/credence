<template>
  <span 
    class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold border"
    :class="badgeClass"
  >
    <span class="w-1.5 h-1.5 rounded-full" :class="dotClass"></span>
    <span>{{ label }}</span>
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  status: {
    type: String,
    required: true
  }
})

const label = computed(() => {
  const map = {
    'NEW': 'New Lead',
    'ASSIGNED': 'Assigned',
    'CONTACT_ATTEMPTED': 'Contact Attempted',
    'CONTACTED': 'Contacted',
    'QUALIFIED': 'Qualified',
    'NOT_QUALIFIED': 'Ineligible',
    'CLOSED_LOST': 'Closed / Lost'
  }
  return map[props.status] || props.status
})

const badgeClass = computed(() => {
  const map = {
    'NEW': 'bg-blue-50 text-blue-800 border-blue-200',
    'ASSIGNED': 'bg-amber-50 text-amber-800 border-amber-200',
    'CONTACT_ATTEMPTED': 'bg-slate-50 text-slate-800 border-slate-200',
    'CONTACTED': 'bg-teal-50 text-teal-800 border-teal-200',
    'QUALIFIED': 'bg-sage/10 text-sage border-sage/20',
    'NOT_QUALIFIED': 'bg-rose-50 text-rose-800 border-rose-200',
    'CLOSED_LOST': 'bg-gray-100 text-gray-700 border-gray-200'
  }
  return map[props.status] || 'bg-surface-secondary text-brand-deep border-surface-border'
})

const dotClass = computed(() => {
  const map = {
    'NEW': 'bg-blue-600',
    'ASSIGNED': 'bg-amber-600',
    'CONTACT_ATTEMPTED': 'bg-slate-600',
    'CONTACTED': 'bg-teal-600',
    'QUALIFIED': 'bg-sage',
    'NOT_QUALIFIED': 'bg-rose-600',
    'CLOSED_LOST': 'bg-gray-500'
  }
  return map[props.status] || 'bg-brand'
})
</script>

