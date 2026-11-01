<template>
  <div class="min-h-screen flex flex-col bg-surface-canvas text-brand-deep">
    <Navbar />

    <main class="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 w-full">
      <div class="max-w-3xl mb-8">
        <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-surface-secondary border border-surface-border text-xs font-semibold text-brand mb-3">
          <Scale class="w-3.5 h-3.5" />
          <span>Side-by-Side Evaluation</span>
        </div>
        <h1 class="text-3xl font-bold font-serif text-brand-deep mb-2">
          Compare Loan Schemes
        </h1>
        <p class="text-sm text-brand-muted">
          Select up to 3 verified products to evaluate benchmark spreads, rate ranges, and maximum tenures side-by-side.
        </p>
      </div>

      <!-- Quick Preset Comparisons -->
      <div class="mb-6 flex items-center gap-2 flex-wrap">
        <span class="text-xs font-semibold text-brand-muted">Popular Comparisons:</span>
        <button
          v-for="(preset, i) in presets"
          :key="i"
          @click="loadPreset(preset)"
          class="text-xs bg-white hover:bg-surface-light border border-surface-border text-brand px-3 py-1 rounded-full transition font-medium"
        >
          {{ preset.label }}
        </button>
      </div>

      <!-- Selectors for 3 Loan Slots -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <div 
          v-for="index in [0, 1, 2]" 
          :key="index"
          class="bg-white p-4 rounded-xl border border-surface-border shadow-xs"
        >
          <div class="flex items-center justify-between mb-2">
            <span class="text-xs font-semibold uppercase tracking-wider text-brand-muted">
              Loan {{ index + 1 }}
            </span>
            <button 
              v-if="selectedSchemes[index]" 
              @click="removeSlot(index)"
              class="text-xs text-brand-muted hover:text-red-600 transition"
            >
              Change
            </button>
          </div>

          <select 
            :value="selectedSchemes[index]?.compact_key || ''"
            @change="onSelectScheme(index, $event.target.value)"
            class="w-full bg-surface-canvas border border-surface-border rounded-lg px-3 py-2 text-xs text-brand-deep focus:outline-none focus:border-brand font-medium truncate"
          >
            <option value="">-- Choose a Bank Scheme --</option>
            <option 
              v-for="s in availableSchemes" 
              :key="s.compact_key" 
              :value="s.compact_key"
            >
              {{ s.institution }} — {{ s.scheme_name }}
            </option>
          </select>
        </div>
      </div>

      <!-- Side-by-Side Comparison Table -->
      <div v-if="activeSelectedCount > 0" class="bg-white rounded-xl border border-surface-border shadow-sm overflow-hidden mb-8">
        <div class="overflow-x-auto">
          <table class="w-full text-left text-xs sm:text-sm">
            <thead class="bg-surface-secondary text-brand-deep border-b border-surface-border">
              <tr>
                <th class="p-4 w-1/4 font-bold text-xs uppercase tracking-wider text-brand-muted">Feature</th>
                <th 
                  v-for="(s, idx) in activeSchemesList" 
                  :key="idx" 
                  class="p-4 w-1/4 font-bold text-brand-deep border-l border-surface-border"
                >
                  <div class="text-xs font-medium text-brand">{{ s.institution }}</div>
                  <div class="text-sm font-bold text-brand-deep">{{ s.scheme_name }}</div>
                </th>
              </tr>
            </thead>
            <tbody class="divide-y divide-surface-border text-brand-deep">
              <tr>
                <td class="p-4 font-semibold text-brand-muted bg-surface-canvas/50">Category</td>
                <td v-for="(s, idx) in activeSchemesList" :key="idx" class="p-4 border-l border-surface-border font-medium">
                  {{ s.category }}
                </td>
              </tr>
              <tr>
                <td class="p-4 font-semibold text-brand-muted bg-surface-canvas/50">Banking Sector</td>
                <td v-for="(s, idx) in activeSchemesList" :key="idx" class="p-4 border-l border-surface-border">
                  {{ s.sector }}
                </td>
              </tr>
              <tr>
                <td class="p-4 font-semibold text-brand-muted bg-surface-canvas/50">Interest Rate Range</td>
                <td v-for="(s, idx) in activeSchemesList" :key="idx" class="p-4 border-l border-surface-border font-bold font-tabular text-brand">
                  {{ s.interest_rate_range || 'Contact lender' }}
                </td>
              </tr>
              <tr>
                <td class="p-4 font-semibold text-brand-muted bg-surface-canvas/50">Benchmark</td>
                <td v-for="(s, idx) in activeSchemesList" :key="idx" class="p-4 border-l border-surface-border font-medium">
                  {{ s.benchmark || 'EBLR / MCLR' }}
                </td>
              </tr>
              <tr>
                <td class="p-4 font-semibold text-brand-muted bg-surface-canvas/50">Max Tenure</td>
                <td v-for="(s, idx) in activeSchemesList" :key="idx" class="p-4 border-l border-surface-border">
                  {{ s.max_tenure_years ? `${s.max_tenure_years} Years` : 'Not specified' }}
                </td>
              </tr>
              <tr>
                <td class="p-4 font-semibold text-brand-muted bg-surface-canvas/50">Maximum Quantum</td>
                <td v-for="(s, idx) in activeSchemesList" :key="idx" class="p-4 border-l border-surface-border font-tabular">
                  {{ s.max_loan_amount || 'Subject to FOIR' }}
                </td>
              </tr>
              <tr>
                <td class="p-4 font-semibold text-brand-muted bg-surface-canvas/50">Official Bank Filing</td>
                <td v-for="(s, idx) in activeSchemesList" :key="idx" class="p-4 border-l border-surface-border">
                  <a 
                    v-if="s.source_url" 
                    :href="s.source_url" 
                    target="_blank" 
                    rel="noopener noreferrer"
                    class="text-xs font-semibold text-brand hover:underline flex items-center gap-1"
                  >
                    <span>View Official Portal</span>
                    <ExternalLink class="w-3 h-3" />
                  </a>
                  <span v-else class="text-brand-muted text-xs">Verified in catalog</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Deep AI Analysis CTA -->
        <div class="p-4 bg-surface-canvas border-t border-surface-border flex flex-col sm:flex-row justify-between items-center gap-3">
          <div class="text-xs text-brand-muted">
            Want a nuanced trade-off analysis of processing fees, foreclosure rules, and qualification ceilings?
          </div>
          <button 
            @click="compareInAdvisor"
            class="bg-brand hover:bg-brand-hover text-white text-xs font-semibold px-4 py-2 rounded-lg transition shadow-sm flex items-center gap-1.5 whitespace-nowrap"
          >
            <Sparkles class="w-3.5 h-3.5 text-sage-light" />
            <span>Ask FinNav to Compare in Detail</span>
          </button>
        </div>
      </div>
    </main>

    <Footer />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Scale, Sparkles, ExternalLink } from 'lucide-vue-next'
import Navbar from '../components/Navbar.vue'
import Footer from '../components/Footer.vue'

const router = useRouter()
const availableSchemes = ref([])
const selectedSchemes = ref([null, null, null])

const presets = [
  {
    label: "SBI Scholar vs Canara Vidya Turant",
    keys: ["sbi_scholar_loan", "canara_vidya_turant"]
  },
  {
    label: "HDFC Regular Home vs SBI Regular Home",
    keys: ["hdfc_home_loan", "sbi_regular_home_loan"]
  },
  {
    label: "HDFC Xpress Car vs SBI Car Loan",
    keys: ["hdfc_xpress_car_loan", "sbi_new_car_loan"]
  }
]

const activeSchemesList = computed(() => {
  return selectedSchemes.value.filter(s => s !== null)
})

const activeSelectedCount = computed(() => {
  return activeSchemesList.value.length
})

const onSelectScheme = (slotIndex, compactKey) => {
  if (!compactKey) {
    selectedSchemes.value[slotIndex] = null
    return
  }
  const found = availableSchemes.value.find(s => s.compact_key === compactKey)
  if (found) {
    selectedSchemes.value[slotIndex] = found
  }
}

const removeSlot = (slotIndex) => {
  selectedSchemes.value[slotIndex] = null
}

const loadPreset = (preset) => {
  selectedSchemes.value = [null, null, null]
  preset.keys.forEach((k, idx) => {
    const match = availableSchemes.value.find(s => s.compact_key?.includes(k) || s.scheme_slug?.includes(k))
    if (match && idx < 3) {
      selectedSchemes.value[idx] = match
    }
  })
}

const compareInAdvisor = () => {
  const names = activeSchemesList.value.map(s => `${s.scheme_name} (${s.institution})`).join(" vs ")
  router.push({
    path: '/advisor',
    query: {
      q: `Compare ${names} in detail: interest rate ranges, benchmark spread, processing fees, and qualification standards.`
    }
  })
}

onMounted(async () => {
  try {
    const res = await fetch('/api/schemes?limit=163')
    if (res.ok) {
      const data = await res.json()
      availableSchemes.value = data.schemes || []

      // Pre-select first 2 popular schemes
      if (availableSchemes.value.length >= 2) {
        selectedSchemes.value[0] = availableSchemes.value[0]
        selectedSchemes.value[1] = availableSchemes.value[1]
      }
    }
  } catch (e) {
    console.error('Failed to load comparison schemes:', e)
  }
})
</script>

