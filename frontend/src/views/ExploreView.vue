<template>
  <div class="min-h-screen flex flex-col bg-surface-canvas text-brand-deep">
    <Navbar />

    <main class="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 w-full">
      <!-- Header -->
      <div class="max-w-3xl mb-8">
        <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-surface-secondary border border-surface-border text-xs font-semibold text-brand mb-3">
          <Layers class="w-3.5 h-3.5" />
          <span>Verified Indian Loan Catalog</span>
        </div>
        <h1 class="text-3xl font-bold font-serif text-brand-deep mb-2">
          Explore 163 Bank Schemes
        </h1>
        <p class="text-sm text-brand-muted">
          Compare interest rates, benchmarks, and quantum limits across 34 top Indian banks & NBFCs. Grounded directly on verified filings.
        </p>
      </div>

      <!-- Filters & Search Toolbar -->
      <div class="bg-white p-4 rounded-xl border border-surface-border shadow-xs mb-8 flex flex-col md:flex-row gap-4 justify-between items-stretch md:items-center">
        <!-- Search Input -->
        <div class="relative flex-1 max-w-md">
          <Search class="w-4 h-4 text-brand-muted absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input 
            v-model="searchQuery"
            @input="fetchSchemes"
            type="text" 
            placeholder="Search by bank name, scheme, or feature (e.g. SBI, Scholar, Doctor)..."
            class="w-full pl-10 pr-4 py-2 bg-surface-canvas border border-surface-border rounded-lg text-xs sm:text-sm text-brand-deep placeholder-brand-muted/70 focus:outline-none focus:border-brand"
          />
        </div>

        <!-- Category & Sector Filters -->
        <div class="flex items-center gap-2 flex-wrap">
          <select 
            v-model="selectedCategory" 
            @change="fetchSchemes"
            class="bg-surface-canvas border border-surface-border rounded-lg px-3 py-2 text-xs text-brand-deep focus:outline-none focus:border-brand font-medium"
          >
            <option value="All">All Categories</option>
            <option value="Home Loan">Home Loan</option>
            <option value="Personal Loan">Personal Loan</option>
            <option value="Education Loan">Education Loan</option>
            <option value="Vehicle Loan">Vehicle Loan</option>
          </select>

          <select 
            v-model="selectedSector" 
            @change="fetchSchemes"
            class="bg-surface-canvas border border-surface-border rounded-lg px-3 py-2 text-xs text-brand-deep focus:outline-none focus:border-brand font-medium"
          >
            <option value="All">All Sectors</option>
            <option value="Public">Public Sector</option>
            <option value="Private">Private Banks</option>
            <option value="NBFC">NBFCs</option>
          </select>
        </div>
      </div>

      <!-- Schemes Grid -->
      <div v-if="loading" class="py-16 text-center text-brand-muted">
        <Loader2 class="w-6 h-6 animate-spin mx-auto mb-2 text-brand" />
        <span class="text-sm">Retrieving catalog schemes...</span>
      </div>

      <div v-else-if="schemes.length === 0" class="py-16 text-center text-brand-muted bg-white rounded-xl border border-surface-border">
        <p class="text-sm font-medium">No matching loan schemes found.</p>
        <p class="text-xs mt-1">Try broadening your search or resetting category filters.</p>
      </div>

      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div 
          v-for="scheme in schemes" 
          :key="scheme.compact_key"
          class="bg-white rounded-xl border border-surface-border hover:border-brand/40 hover:shadow-md transition p-5 flex flex-col justify-between"
        >
          <div>
            <!-- Top Tags -->
            <div class="flex items-center justify-between text-xs mb-2">
              <span class="font-semibold text-brand px-2 py-0.5 rounded bg-surface-light border border-brand/20">
                {{ scheme.category }}
              </span>
              <span class="text-brand-muted text-[11px]">
                {{ scheme.sector }} Sector
              </span>
            </div>

            <!-- Title & Bank -->
            <h3 class="text-base font-bold text-brand-deep mb-0.5">
              {{ scheme.scheme_name }}
            </h3>
            <p class="text-xs text-brand-muted mb-4 font-medium">
              {{ scheme.institution }}
            </p>

            <!-- Metrics -->
            <div class="grid grid-cols-2 gap-2 p-3 rounded-lg bg-surface-canvas border border-surface-border text-xs mb-4">
              <div>
                <span class="text-[11px] text-brand-muted block">Interest Rate:</span>
                <span class="font-bold font-tabular text-brand-deep">{{ scheme.interest_rate_range || 'Subject to risk' }}</span>
              </div>
              <div>
                <span class="text-[11px] text-brand-muted block">Benchmark:</span>
                <span class="font-medium text-brand-deep">{{ scheme.benchmark || 'EBLR / MCLR' }}</span>
              </div>
              <div v-if="scheme.max_tenure_years">
                <span class="text-[11px] text-brand-muted block">Max Tenure:</span>
                <span class="font-medium">{{ scheme.max_tenure_years }} Years</span>
              </div>
              <div v-if="scheme.max_loan_amount">
                <span class="text-[11px] text-brand-muted block">Max Quantum:</span>
                <span class="font-medium truncate">{{ scheme.max_loan_amount }}</span>
              </div>
            </div>
          </div>

          <!-- Bottom Actions -->
          <div class="pt-3 border-t border-surface-border flex items-center justify-between gap-2">
            <button 
              @click="askAdvisorAboutScheme(scheme)"
              class="text-xs font-semibold text-brand hover:text-brand-hover flex items-center gap-1.5 transition"
            >
              <Sparkles class="w-3.5 h-3.5 text-sage" />
              <span>Ask Credence</span>
            </button>

            <a 
              v-if="scheme.source_url" 
              :href="scheme.source_url" 
              target="_blank" 
              rel="noopener noreferrer"
              class="text-xs text-brand-muted hover:text-brand-deep flex items-center gap-1 font-medium transition"
            >
              <span>Bank Portal</span>
              <ExternalLink class="w-3 h-3" />
            </a>
          </div>
        </div>
      </div>
    </main>

    <Footer />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { 
  Layers, 
  Search, 
  Sparkles, 
  ExternalLink, 
  Loader2 
} from 'lucide-vue-next'
import Navbar from '../components/Navbar.vue'
import Footer from '../components/Footer.vue'

const router = useRouter()
const route = useRoute()

const schemes = ref([])
const loading = ref(true)
const searchQuery = ref('')
const selectedCategory = ref(route.query.category || 'All')
const selectedSector = ref('All')

const fetchSchemes = async () => {
  loading.value = true
  try {
    const params = new URLSearchParams()
    if (selectedCategory.value !== 'All') params.append('category', selectedCategory.value)
    if (selectedSector.value !== 'All') params.append('sector', selectedSector.value)
    if (searchQuery.value.trim()) params.append('search', searchQuery.value.trim())
    params.append('limit', '60')

    const res = await fetch(`/api/schemes?${params.toString()}`)
    if (res.ok) {
      const data = await res.json()
      schemes.value = data.schemes || []
    }
  } catch (e) {
    console.error('Failed to fetch schemes:', e)
  } finally {
    loading.value = false
  }
}

const askAdvisorAboutScheme = (scheme) => {
  router.push({
    path: '/advisor',
    query: {
      q: `Give me a full breakdown of ${scheme.scheme_name} from ${scheme.institution}: interest rates, benchmark, and eligibility criteria.`
    }
  })
}

onMounted(() => {
  fetchSchemes()
})
</script>

