<template>
  <div class="min-h-screen flex flex-col bg-surface-canvas text-brand-deep">
    <Navbar />

    <!-- Section 2: Hero -->
    <section class="pt-12 pb-16 md:pt-20 md:pb-24 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto w-full">
      <div class="max-w-3xl mx-auto text-center space-y-4 mb-8">
        <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-surface-secondary border border-surface-border text-xs font-semibold text-brand">
          <ShieldCheck class="w-3.5 h-3.5 text-sage" />
          <span>163 Bank Schemes · Grounded Indian RAG · 100% Free</span>
        </div>
        <h1 class="text-3xl sm:text-4xl md:text-5xl font-bold font-serif tracking-tight text-brand-deep leading-tight">
          Find the right loan.<br />
          <span class="text-brand">Understand every rupee.</span>
        </h1>
        <p class="text-base sm:text-lg text-brand-muted leading-relaxed max-w-2xl mx-auto">
          Compare verified bank schemes, test your eligibility without sales calls, and make confident borrowing decisions guided by deterministic AI.
        </p>
      </div>

      <!-- Interactive Loan Discovery Box (Launches /advisor) -->
      <div class="max-w-2xl mx-auto bg-white rounded-2xl border border-surface-border shadow-lg p-4 sm:p-6 transition hover:shadow-xl">
        <!-- Category Pill Selectors -->
        <div class="flex items-center gap-2 overflow-x-auto pb-3 mb-3 border-b border-surface-border text-xs font-medium text-brand-muted no-scrollbar">
          <span class="text-brand-deep font-semibold whitespace-nowrap">Category:</span>
          <button 
            v-for="cat in categories" 
            :key="cat"
            @click="selectedCategory = cat"
            class="px-3 py-1 rounded-full transition whitespace-nowrap"
            :class="selectedCategory === cat ? 'bg-brand text-white font-semibold' : 'bg-surface-secondary hover:bg-surface-border text-brand-deep'"
          >
            {{ cat }}
          </button>
        </div>

        <!-- Conversational Input -->
        <div class="relative flex flex-col sm:flex-row gap-2">
          <input 
            v-model="heroQuery"
            @keydown.enter="launchAdvisor"
            type="text" 
            placeholder="e.g., I need a ₹40 Lakh home loan and earn ₹80,000 / month" 
            class="w-full bg-surface-canvas border border-surface-border rounded-xl px-4 py-3.5 text-sm text-brand-deep placeholder-brand-muted/70 focus:outline-none focus:border-brand focus:ring-1 focus:ring-brand transition"
          />
          <button 
            @click="launchAdvisor"
            class="sm:flex-shrink-0 bg-brand hover:bg-brand-hover text-white text-sm font-semibold px-6 py-3.5 rounded-xl transition shadow flex items-center justify-center gap-2"
          >
            <span>Explore Options</span>
            <ArrowRight class="w-4 h-4" />
          </button>
        </div>

        <!-- Quick Suggestions -->
        <div class="flex items-center gap-2 mt-3 text-xs text-brand-muted flex-wrap">
          <span class="font-medium text-brand-deep">Try:</span>
          <button 
            v-for="(p, i) in samplePrompts" 
            :key="i"
            @click="selectPrompt(p)"
            class="text-brand-link hover:underline text-left truncate max-w-[200px]"
          >
            "{{ p }}"
          </button>
        </div>
      </div>
    </section>

    <!-- Section 3: Trust & Value Proposition -->
    <section class="py-14 bg-surface-secondary border-y border-surface-border">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center max-w-2xl mx-auto mb-10">
          <h2 class="text-2xl sm:text-3xl font-bold font-serif text-brand-deep mb-2">
            Borrow with clarity, not confusion.
          </h2>
          <p class="text-sm text-brand-muted">
            Traditional loan portals sell your phone number to telecallers. FinNav is built on strict data grounding, zero spam, and mathematical precision.
          </p>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          <div class="bg-white p-6 rounded-xl border border-surface-border shadow-sm">
            <div class="w-10 h-10 rounded-lg bg-surface-light text-brand flex items-center justify-center mb-4">
              <FileText class="w-5 h-5" />
            </div>
            <h3 class="text-base font-semibold text-brand-deep mb-1">Source-Backed Schemes</h3>
            <p class="text-xs text-brand-muted leading-relaxed">
              Every rate range and condition links directly to official bank filings from SBI, HDFC, ICICI, and RBI circulars.
            </p>
          </div>

          <div class="bg-white p-6 rounded-xl border border-surface-border shadow-sm">
            <div class="w-10 h-10 rounded-lg bg-surface-light text-brand flex items-center justify-center mb-4">
              <Scale class="w-5 h-5" />
            </div>
            <h3 class="text-base font-semibold text-brand-deep mb-1">Unbiased Comparisons</h3>
            <p class="text-xs text-brand-muted leading-relaxed">
              Transparent side-by-side benchmarking of EBLR vs MCLR spreads, processing charges, and prepayment terms.
            </p>
          </div>

          <div class="bg-white p-6 rounded-xl border border-surface-border shadow-sm">
            <div class="w-10 h-10 rounded-lg bg-surface-light text-brand flex items-center justify-center mb-4">
              <Calculator class="w-5 h-5" />
            </div>
            <h3 class="text-base font-semibold text-brand-deep mb-1">Deterministic EMI</h3>
            <p class="text-xs text-brand-muted leading-relaxed">
              No hallucinatory figures. All amortizations, FOIR ceilings, and payment ratios are computed deterministically.
            </p>
          </div>

          <div class="bg-white p-6 rounded-xl border border-surface-border shadow-sm">
            <div class="w-10 h-10 rounded-lg bg-sage-light text-sage flex items-center justify-center mb-4">
              <Lock class="w-5 h-5" />
            </div>
            <h3 class="text-base font-semibold text-brand-deep mb-1">100% Privacy & Free</h3>
            <p class="text-xs text-brand-muted leading-relaxed">
              No mandatory phone numbers, no spam OTPs, and no aggressive lender agent follow-ups.
            </p>
          </div>
        </div>
      </div>
    </section>

    <!-- Section 4: How FinNav Works -->
    <section class="py-16 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 w-full">
      <div class="text-center max-w-2xl mx-auto mb-12">
        <h2 class="text-2xl sm:text-3xl font-bold font-serif text-brand-deep mb-2">
          How FinNav Works
        </h2>
        <p class="text-sm text-brand-muted">
          From first question to lender execution in three straightforward steps.
        </p>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
        <div class="flex flex-col items-center text-center space-y-3">
          <div class="w-12 h-12 rounded-full bg-brand text-white font-bold flex items-center justify-center text-lg shadow-md">
            1
          </div>
          <h3 class="text-base font-semibold text-brand-deep">Tell Us What You Need</h3>
          <p class="text-xs text-brand-muted leading-relaxed max-w-xs">
            Ask in plain conversational English about your target amount, income, credit profile, or bank preferences.
          </p>
        </div>

        <div class="flex flex-col items-center text-center space-y-3">
          <div class="w-12 h-12 rounded-full bg-brand text-white font-bold flex items-center justify-center text-lg shadow-md">
            2
          </div>
          <h3 class="text-base font-semibold text-brand-deep">Discover & Compare Grounded Schemes</h3>
          <p class="text-xs text-brand-muted leading-relaxed max-w-xs">
            Our LangGraph engine queries 163 verified products across 34 top Indian institutions with verified portal links.
          </p>
        </div>

        <div class="flex flex-col items-center text-center space-y-3">
          <div class="w-12 h-12 rounded-full bg-brand text-white font-bold flex items-center justify-center text-lg shadow-md">
            3
          </div>
          <h3 class="text-base font-semibold text-brand-deep">Decide with Confidence</h3>
          <p class="text-xs text-brand-muted leading-relaxed max-w-xs">
            Understand key fact statements, tax deductions (like Section 80E), and exact EMI impact before applying.
          </p>
        </div>
      </div>
    </section>

    <!-- Section 5: Loan Categories -->
    <section class="py-14 bg-surface-secondary border-t border-surface-border">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex flex-col sm:flex-row justify-between items-start sm:items-end mb-8 gap-4">
          <div>
            <h2 class="text-2xl sm:text-3xl font-bold font-serif text-brand-deep mb-1">
              Explore Verified Loan Categories
            </h2>
            <p class="text-sm text-brand-muted">
              Covering 34 public, private, and NBFC lenders in India.
            </p>
          </div>
          <router-link to="/explore" class="text-sm font-semibold text-brand-link hover:text-brand flex items-center gap-1">
            <span>View All 163 Schemes</span>
            <ArrowRight class="w-4 h-4" />
          </router-link>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          <div 
            v-for="card in categoryCards" 
            :key="card.title"
            class="bg-white rounded-xl border border-surface-border p-5 hover:border-brand transition shadow-sm flex flex-col justify-between"
          >
            <div>
              <div class="text-2xl mb-3">{{ card.icon }}</div>
              <h3 class="text-base font-semibold text-brand-deep mb-1">{{ card.title }}</h3>
              <p class="text-xs text-brand-muted mb-4 leading-relaxed">{{ card.desc }}</p>
              <div class="text-[11px] font-mono text-brand font-medium mb-4 bg-surface-light px-2.5 py-1 rounded inline-block">
                {{ card.rate }}
              </div>
            </div>
            <router-link 
              :to="card.link"
              class="text-xs font-semibold text-brand hover:text-brand-hover flex items-center gap-1 pt-3 border-t border-surface-border"
            >
              <span>Explore Schemes</span>
              <ArrowRight class="w-3.5 h-3.5" />
            </router-link>
          </div>
        </div>
      </div>
    </section>

    <!-- Section 6: Knowledge Hub Preview -->
    <section class="py-16 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 w-full">
      <div class="flex flex-col sm:flex-row justify-between items-start sm:items-end mb-8 gap-4">
        <div>
          <span class="text-xs font-semibold uppercase tracking-wider text-brand">FinNav Learn</span>
          <h2 class="text-2xl sm:text-3xl font-bold font-serif text-brand-deep mt-1">
            A little knowledge can save you a lot of money.
          </h2>
        </div>
        <router-link to="/learn" class="text-sm font-semibold text-brand-link hover:text-brand flex items-center gap-1">
          <span>Explore Knowledge Hub</span>
          <ArrowRight class="w-4 h-4" />
        </router-link>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div 
          v-for="article in featuredArticles" 
          :key="article.slug"
          class="bg-white rounded-xl border border-surface-border p-6 shadow-sm hover:shadow-md transition flex flex-col justify-between"
        >
          <div>
            <div class="flex justify-between items-center text-xs text-brand-muted mb-2">
              <span class="font-medium text-brand">{{ article.category }}</span>
              <span>{{ article.readTime }}</span>
            </div>
            <h3 class="text-base font-bold font-serif text-brand-deep mb-2 hover:text-brand transition">
              {{ article.title }}
            </h3>
            <p class="text-xs text-brand-muted leading-relaxed mb-4">
              {{ article.excerpt }}
            </p>
          </div>
          <router-link 
            :to="`/learn?article=${article.slug}`"
            class="text-xs font-semibold text-brand-link hover:text-brand flex items-center gap-1 pt-3 border-t border-surface-border"
          >
            <span>Read Article</span>
            <ArrowRight class="w-3.5 h-3.5" />
          </router-link>
        </div>
      </div>
    </section>

    <!-- Section 7: Final CTA -->
    <section class="py-16 bg-surface-ivory border-t border-surface-border">
      <div class="max-w-4xl mx-auto px-4 text-center space-y-4">
        <h2 class="text-2xl sm:text-3xl font-bold font-serif text-brand-deep">
          Have a loan question? Ask FinNav.
        </h2>
        <p class="text-sm text-brand-muted max-w-xl mx-auto">
          Understand your borrowing options, compare lenders side-by-side, and make an informed decision without aggressive sales pitches.
        </p>
        <div class="pt-2">
          <router-link 
            to="/advisor" 
            class="inline-flex items-center gap-2 bg-brand hover:bg-brand-hover text-white text-sm font-semibold px-6 py-3 rounded-xl transition shadow"
          >
            <Sparkles class="w-4 h-4 text-sage-light" />
            <span>Talk to FinNav Advisor</span>
          </router-link>
        </div>
      </div>
    </section>

    <Footer />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { 
  ShieldCheck, 
  ArrowRight, 
  FileText, 
  Scale, 
  Calculator, 
  Lock, 
  Sparkles 
} from 'lucide-vue-next'
import Navbar from '../components/Navbar.vue'
import Footer from '../components/Footer.vue'

const router = useRouter()
const heroQuery = ref('')
const selectedCategory = ref('Home Loan')

const categories = ['Home Loan', 'Personal Loan', 'Education Loan', 'Vehicle Loan']

const samplePrompts = [
  "Compare SBI Scholar vs Canara Vidya Turant",
  "Calculate EMI for 20 Lakhs at 8.75% for 7 years",
  "Doctor wanting flexible overdraft personal loan"
]

const categoryCards = [
  {
    title: 'Home Loans',
    icon: '🏡',
    desc: 'Regular, MaxGain overdraft, affordable PMAY schemes, and plot purchase financing.',
    rate: 'Starting @ 8.40% p.a.',
    link: '/explore?category=Home+Loan'
  },
  {
    title: 'Personal Loans',
    icon: '💳',
    desc: 'Unsecured credit lines, doctor overdrafts, emergency liquidity, and salary advance.',
    rate: 'Starting @ 10.25% p.a.',
    link: '/explore?category=Personal+Loan'
  },
  {
    title: 'Education Loans',
    icon: '🎓',
    desc: 'Premier institute schemes (SBI Scholar), Vidya Turant, and 100% Section 80E tax deductions.',
    rate: 'Starting @ 8.15% p.a.',
    link: '/explore?category=Education+Loan'
  },
  {
    title: 'Vehicle Loans',
    icon: '🚗',
    desc: '100% on-road funding for electric and new cars with flexible 84-month repayment tenures.',
    rate: 'Starting @ 8.65% p.a.',
    link: '/explore?category=Vehicle+Loan'
  }
]

const featuredArticles = [
  {
    slug: 'home-loan-bad-debt',
    category: 'Home Ownership',
    readTime: '4 min read',
    title: 'Is Taking a Home Loan Actually Bad Debt?',
    excerpt: 'Examining tax offsets under Section 24(b), inflation amortization, and how to evaluate leverage against alternative equity investments.'
  },
  {
    slug: 'eblr-vs-mclr',
    category: 'Loan Basics',
    readTime: '5 min read',
    title: 'EBLR vs MCLR: Why the Benchmark Matters',
    excerpt: 'How RBI mandate of 2019 protects retail floating-rate borrowers and why external benchmarks transmit repo rate cuts faster.'
  },
  {
    slug: 'real-cost-of-loan',
    category: 'Before You Borrow',
    readTime: '3 min read',
    title: 'Your EMI Is Not the Real Cost of Your Loan',
    excerpt: 'Decoding processing fees, MODT charges, administrative levies, and insurance bundlings that inflate borrowing expenses.'
  }
]

const selectPrompt = (prompt) => {
  heroQuery.value = prompt
  launchAdvisor()
}

const launchAdvisor = () => {
  const query = heroQuery.value.trim()
  router.push({
    path: '/advisor',
    query: {
      q: query || undefined,
      category: selectedCategory.value !== 'All' ? selectedCategory.value : undefined
    }
  })
}
</script>

