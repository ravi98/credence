<template>
  <div class="max-w-2xl mx-auto px-4 py-8 text-center">
    <!-- Header -->
    <div class="inline-flex p-3 rounded-2xl bg-surface-light border border-brand/20 text-brand mb-4 shadow-xs">
      <Landmark class="w-8 h-8" />
    </div>
    <h1 class="text-2xl sm:text-3xl font-bold font-serif tracking-tight text-brand-deep mb-2">
      How can I help you today?
    </h1>
    <p class="text-sm text-brand-muted max-w-lg mx-auto mb-8 leading-relaxed">
      Understand loan terms, check your borrowing eligibility, or compare verified schemes across 34 top Indian banks.
    </p>

    <!-- 4 Primary Interaction Cards -->
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 text-left mb-6">
      <button
        v-for="(card, idx) in primaryCards"
        :key="idx"
        @click="$emit('select-prompt', card.prompt)"
        class="group p-4 rounded-xl border border-surface-border bg-white hover:border-brand/40 hover:shadow-sm transition text-left flex flex-col justify-between"
      >
        <div class="flex items-center justify-between w-full mb-2">
          <span class="text-lg">{{ card.icon }}</span>
          <ArrowUpRight class="w-4 h-4 text-brand-muted group-hover:text-brand group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition" />
        </div>
        <div>
          <h3 class="text-sm font-semibold text-brand-deep group-hover:text-brand transition">
            {{ card.title }}
          </h3>
          <p class="text-xs text-brand-muted line-clamp-2 mt-0.5">
            {{ card.desc }}
          </p>
        </div>
      </button>
    </div>

    <!-- Category Shortcuts -->
    <div class="flex items-center justify-center gap-2 flex-wrap">
      <span class="text-xs text-brand-muted font-medium">Category shortcuts:</span>
      <button
        v-for="cat in categoryShortcuts"
        :key="cat"
        @click="$emit('select-category', cat)"
        class="text-xs bg-surface-secondary hover:bg-surface-border text-brand-deep px-3 py-1 rounded-full border border-surface-border transition font-medium"
      >
        {{ cat }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { Landmark, ArrowUpRight } from 'lucide-vue-next'

const primaryCards = [
  {
    icon: '🔍',
    title: 'Find a Loan',
    desc: 'Discover verified options tailored to your income and requirements.',
    prompt: 'Find the best loan schemes for my profile'
  },
  {
    icon: '📋',
    title: 'Check My Eligibility',
    desc: 'Understand your borrowing capacity, FOIR ceilings, and criteria.',
    prompt: 'Check my loan eligibility and borrowing capacity'
  },
  {
    icon: '⚖️',
    title: 'Compare Bank Loans',
    desc: 'Compare rates, EBLR spreads, and processing fees side-by-side.',
    prompt: 'Compare top bank home loans side-by-side'
  },
  {
    icon: '📚',
    title: 'Understand a Loan',
    desc: 'Clear answers on benchmarks (EBLR vs MCLR), tax rules, and hidden fees.',
    prompt: 'Explain what is EBLR vs MCLR and which benchmark is better'
  }
]

const categoryShortcuts = [
  'Home Loan',
  'Personal Loan',
  'Education Loan',
  'Vehicle Loan'
]

defineEmits(['select-prompt', 'select-category'])
</script>

