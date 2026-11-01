<template>
  <div class="max-w-2xl mx-auto px-4 py-8 text-center">
    <!-- Hero Icon & Title -->
    <div class="inline-flex p-3 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 mb-4 shadow-inner">
      <Landmark class="w-8 h-8" />
    </div>
    <h1 class="text-2xl md:text-3xl font-bold tracking-tight text-white mb-2">
      FinNav — Indian Loan Advisor AI
    </h1>
    <p class="text-sm md:text-base text-gray-400 max-w-lg mx-auto mb-8">
      Grounded on 163 verified retail schemes across 34 top Indian banks & NBFCs with deterministic calculations and zero hallucination.
    </p>

    <!-- Suggestion Cards Grid -->
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 text-left">
      <button
        v-for="(item, idx) in prompts"
        :key="idx"
        @click="$emit('select-prompt', item.prompt)"
        class="group p-3.5 rounded-xl border border-white/10 bg-[#262626] hover:bg-[#2f2f2f] hover:border-emerald-500/40 transition duration-150 flex flex-col justify-between"
      >
        <div class="flex items-center justify-between w-full mb-1.5">
          <span class="text-xs font-medium text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
            {{ item.badge }}
          </span>
          <ArrowUpRight class="w-4 h-4 text-gray-500 group-hover:text-emerald-400 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition" />
        </div>
        <div>
          <p class="text-sm font-semibold text-gray-200 group-hover:text-white">
            {{ item.title }}
          </p>
          <p class="text-xs text-gray-400 line-clamp-1 mt-0.5">
            {{ item.prompt }}
          </p>
        </div>
      </button>
    </div>
  </div>
</template>

<script setup>
import { Landmark, ArrowUpRight } from 'lucide-vue-next'

defineProps({
  prompts: {
    type: Array,
    default: () => [
      {
        title: "Compare Education Loans",
        prompt: "Compare SBI Scholar Loan vs Canara Vidya Turant",
        badge: "Comparison"
      },
      {
        title: "EBLR vs MCLR Benchmark",
        prompt: "What is EBLR vs MCLR and which is better?",
        badge: "Regulation"
      },
      {
        title: "Calculate Loan EMI",
        prompt: "Calculate EMI for 20 Lakhs at 8.75% for 7 years",
        badge: "Calculator"
      },
      {
        title: "Doctor Overdraft Loan",
        prompt: "Doctor wanting flexible overdraft personal loan",
        badge: "Advisory"
      }
    ]
  }
})

defineEmits(['select-prompt'])
</script>

