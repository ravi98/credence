<template>
  <div class="min-h-screen flex flex-col bg-surface-canvas text-brand-deep">
    <Navbar />

    <main class="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 w-full">
      <!-- Hub Header -->
      <div class="max-w-3xl mb-10">
        <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-surface-secondary border border-surface-border text-xs font-semibold text-brand mb-3">
          <BookOpen class="w-3.5 h-3.5" />
          <span>Credence Learn — Borrow Better. Understand More.</span>
        </div>
        <h1 class="text-3xl sm:text-4xl font-bold font-serif text-brand-deep mb-2">
          Everything you should know before taking a loan.
        </h1>
        <p class="text-sm text-brand-muted leading-relaxed">
          Unbiased, research-backed guides on Indian banking regulations, credit scoring, tax benefits, and total cost of borrowing.
        </p>
      </div>

      <!-- Categories Filter -->
      <div class="flex items-center gap-2 overflow-x-auto pb-4 mb-8 border-b border-surface-border text-xs font-medium no-scrollbar">
        <button 
          v-for="cat in categories" 
          :key="cat"
          @click="selectedCategory = cat"
          class="px-3.5 py-1.5 rounded-full transition whitespace-nowrap"
          :class="selectedCategory === cat ? 'bg-brand text-white font-semibold' : 'bg-white hover:bg-surface-secondary text-brand-deep border border-surface-border'"
        >
          {{ cat }}
        </button>
      </div>

      <!-- Articles Grid -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12">
        <article 
          v-for="art in filteredArticles" 
          :key="art.slug"
          class="bg-white rounded-xl border border-surface-border hover:border-brand/40 shadow-xs hover:shadow-md transition p-6 flex flex-col justify-between"
        >
          <div>
            <div class="flex items-center justify-between text-xs text-brand-muted mb-2.5">
              <span class="font-semibold text-brand px-2 py-0.5 rounded bg-surface-light border border-brand/20">
                {{ art.category }}
              </span>
              <span class="text-[11px]">{{ art.readTime }}</span>
            </div>

            <h2 class="text-lg font-bold font-serif text-brand-deep mb-2.5 leading-snug hover:text-brand transition cursor-pointer" @click="activeArticle = art">
              {{ art.title }}
            </h2>

            <p class="text-xs text-brand-muted leading-relaxed mb-4">
              {{ art.excerpt }}
            </p>
          </div>

          <div class="pt-4 border-t border-surface-border flex items-center justify-between">
            <button 
              @click="activeArticle = art"
              class="text-xs font-semibold text-brand hover:text-brand-hover flex items-center gap-1"
            >
              <span>Read Full Guide</span>
              <ArrowRight class="w-3.5 h-3.5" />
            </button>
            <button 
              @click="discussInAdvisor(art)"
              class="text-xs text-brand-muted hover:text-brand flex items-center gap-1 font-medium"
              title="Discuss with Credence Advisor"
            >
              <Sparkles class="w-3 h-3 text-sage" />
              <span>Ask Advisor</span>
            </button>
          </div>
        </article>
      </div>
    </main>

    <!-- Reading Modal / Drawer -->
    <div 
      v-if="activeArticle"
      class="fixed inset-0 bg-brand-deep/50 backdrop-blur-xs z-50 flex items-center justify-center p-4 sm:p-6"
      @click.self="activeArticle = null"
    >
      <div class="bg-white w-full max-w-2xl rounded-2xl shadow-2xl border border-surface-border max-h-[90vh] flex flex-col overflow-hidden">
        <!-- Modal Header -->
        <div class="p-6 border-b border-surface-border flex items-start justify-between bg-surface-canvas">
          <div>
            <div class="flex items-center gap-2 text-xs text-brand mb-1">
              <span class="font-semibold">{{ activeArticle.category }}</span>
              <span>·</span>
              <span>{{ activeArticle.readTime }}</span>
            </div>
            <h2 class="text-xl sm:text-2xl font-bold font-serif text-brand-deep">
              {{ activeArticle.title }}
            </h2>
          </div>
          <button 
            @click="activeArticle = null" 
            class="p-2 text-brand-muted hover:text-brand-deep rounded-lg hover:bg-surface-secondary"
          >
            <X class="w-5 h-5" />
          </button>
        </div>

        <!-- Article Body -->
        <div class="p-6 overflow-y-auto space-y-4 text-sm leading-relaxed text-brand-deep">
          <div class="bg-surface-ivory p-4 rounded-xl border border-surface-border text-xs text-brand-muted leading-relaxed">
            <strong>Key Summary:</strong> {{ activeArticle.excerpt }}
          </div>

          <div class="space-y-3" v-html="activeArticle.content"></div>
        </div>

        <!-- Modal Footer CTA -->
        <div class="p-4 border-t border-surface-border bg-surface-canvas flex flex-col sm:flex-row items-center justify-between gap-3">
          <div class="text-xs text-brand-muted">
            Want to see how this applies to your income and borrowing goals?
          </div>
          <button 
            @click="discussInAdvisor(activeArticle)"
            class="bg-brand hover:bg-brand-hover text-white text-xs font-semibold px-4 py-2 rounded-lg transition shadow-sm flex items-center gap-2 whitespace-nowrap"
          >
            <Sparkles class="w-3.5 h-3.5 text-sage-light" />
            <span>Discuss with Credence Advisor</span>
          </button>
        </div>
      </div>
    </div>

    <Footer />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { BookOpen, ArrowRight, Sparkles, X } from 'lucide-vue-next'
import Navbar from '../components/Navbar.vue'
import Footer from '../components/Footer.vue'

const router = useRouter()
const selectedCategory = ref('All')
const activeArticle = ref(null)

const categories = [
  'All',
  'Home Ownership',
  'Loan Basics',
  'Credit & Eligibility',
  'Tax & Regulation'
]

const articles = [
  {
    slug: 'home-loan-bad-debt',
    category: 'Home Ownership',
    readTime: '4 min read',
    title: 'Is Taking a Home Loan Actually Bad Debt?',
    excerpt: 'Examining tax offsets under Section 24(b), inflation amortization, and how to evaluate leverage against alternative equity investments.',
    content: `
      <p>In consumer finance folklore, debt is often bifurcated into 'good debt' (that builds appreciating assets) and 'bad debt' (lifestyle loans). Home loans occupy a unique position in Indian personal finance due to structural inflation and tax incentives.</p>
      <h3 class="font-bold text-base mt-3">1. The Inflation Hedge</h3>
      <p>Unlike personal loans with short horizons, a 20-year home loan benefits from monetary inflation. While your principal repayment is fixed (or floats marginally around repo rate cycles), your nominal income typically increases over decades, steadily reducing the real burden of the EMI.</p>
      <h3 class="font-bold text-base mt-3">2. Section 24(b) and 80C Deductions</h3>
      <p>Under the Old Tax Regime, interest deductions up to ₹2 Lakh per financial year under Section 24(b) effectively reduce net borrowing costs for taxpayers in the 30% slab by up to ~1.5% - 2.0% on effective yield.</p>
      <h3 class="font-bold text-base mt-3">3. When It Becomes Risky</h3>
      <p>A home loan turns dangerous when the Fixed Obligation to Income Ratio (FOIR) exceeds 50%, or when buyers exhaust all emergency liquidity on the down payment without preserving 6 months of living expenses.</p>
    `
  },
  {
    slug: 'eblr-vs-mclr',
    category: 'Loan Basics',
    readTime: '5 min read',
    title: 'EBLR vs MCLR: Why the External Benchmark Mandate Matters',
    excerpt: 'How RBI mandate of October 2019 protects retail floating-rate borrowers and why external benchmarks transmit repo rate cuts faster.',
    content: `
      <p>Prior to October 2019, commercial banks in India priced retail loans against internal benchmarks: first the Base Rate, then the Marginal Cost of Funds based Lending Rate (MCLR). Under MCLR, banks were notorious for quickly raising interest rates when repo rates rose, but dragging their feet when the RBI slashed rates.</p>
      <h3 class="font-bold text-base mt-3">1. The External Benchmark Lending Rate (EBLR)</h3>
      <p>By RBI mandate, all floating-rate personal, home, and auto loans sanctioned after October 1, 2019 by commercial banks must be tied to an external benchmark—most commonly the RBI Policy Repo Rate.</p>
      <h3 class="font-bold text-base mt-3">2. Mandatory 3-Month Reset</h3>
      <p>Under EBLR, banks are legally mandated to reset the interest rate at least once every three months whenever the benchmark changes. This guarantees 100% transparent transmission without administrative arbitrariness.</p>
      <h3 class="font-bold text-base mt-3">3. NBFC Caveat</h3>
      <p>Note that Housing Finance Companies (HFCs) and NBFCs (like Bajaj Finance or Tata Capital) are regulated differently and still price loans on their internal Prime Lending Rate (PLR). Always verify whether your lender is bound by RBI EBLR mandates.</p>
    `
  },
  {
    slug: 'real-cost-of-loan',
    category: 'Loan Basics',
    readTime: '3 min read',
    title: 'Your EMI Is Not the Real Cost of Your Loan',
    excerpt: 'Decoding processing fees, MODT charges, administrative levies, and insurance bundlings that inflate borrowing expenses.',
    content: `
      <p>When shopping for loans, borrowers obsess over the advertised interest rate (e.g. 8.40% vs 8.55%). However, upfront transaction charges frequently exceed the small difference in rate spread.</p>
      <h3 class="font-bold text-base mt-3">Key Ancillary Costs to Audit:</h3>
      <ul class="list-disc pl-5 space-y-1">
        <li><strong>Processing Fees:</strong> Typically 0.25% to 1.00% of loan quantum (+ 18% GST). On a ₹50 Lakh loan, a 0.5% fee equals ₹29,500.</li>
        <li><strong>Memorandum of Deposit of Title Deeds (MODT):</strong> State stamp duty charged on mortgage registration (0.1% to 0.5% depending on state laws).</li>
        <li><strong>Mandatory Property & Term Insurance:</strong> Some lenders aggressively bundle single-premium credit protect policies into the sanctioned loan amount, inflating interest compoundment.</li>
      </ul>
    `
  },
  {
    slug: 'cibil-750-myth',
    category: 'Credit & Eligibility',
    readTime: '4 min read',
    title: 'Does a 750 CIBIL Score Guarantee Loan Approval?',
    excerpt: 'Why credit bureaus only provide half the picture and how bank underwriting models evaluate debt-to-income and employment stability.',
    content: `
      <p>A CIBIL or Experian score of 750+ qualifies an applicant for prime tier rates. However, credit score only measures your historical repayment discipline—not your forward capacity to service additional debt.</p>
      <h3 class="font-bold text-base mt-3">The Underwriting Trifecta:</h3>
      <ol class="list-decimal pl-5 space-y-1">
        <li><strong>CIBIL Score:</strong> Pass/fail gatekeeper for risk tiering.</li>
        <li><strong>FOIR (Fixed Obligation to Income Ratio):</strong> Banks will not allow total monthly obligations (existing EMIs + proposed EMI) to exceed 50% to 65% of net monthly income.</li>
        <li><strong>Employer Category:</strong> Category A corporate employees and government officials receive lower risk margins than unlisted firms or self-employed applicants with fluctuating cashflows.</li>
      </ol>
    `
  },
  {
    slug: 'section-80e-education-loans',
    category: 'Tax & Regulation',
    readTime: '4 min read',
    title: 'Section 80E: How Education Loans Save Income Tax',
    excerpt: 'Unlike home loan caps, Section 80E allows 100% deduction on interest paid with no upper monetary ceiling for 8 consecutive years.',
    content: `
      <p>Education loans are uniquely subsidized under the Indian Income Tax Act. Under Section 80E, the entire amount of interest paid towards an education loan taken for higher studies (India or abroad) can be deducted from gross total income.</p>
      <h3 class="font-bold text-base mt-3">Key Provisions:</h3>
      <ul class="list-disc pl-5 space-y-1">
        <li><strong>No Upper Limit:</strong> Unlike Section 24(b)'s ₹2 Lakh cap on housing, Section 80E has NO monetary ceiling on deductible interest.</li>
        <li><strong>8-Year Window:</strong> The deduction is available starting the year you begin repayment and for the 7 subsequent financial years.</li>
        <li><strong>Authorized Lenders Only:</strong> The loan must be taken from a scheduled bank or approved financial institution (not informal personal loans).</li>
      </ul>
    `
  }
]

const filteredArticles = computed(() => {
  if (selectedCategory.value === 'All') return articles
  return articles.filter(a => a.category === selectedCategory.value)
})

const discussInAdvisor = (article) => {
  router.push({
    path: '/advisor',
    query: {
      q: `I read your guide '${article.title}'. Can you explain how this applies to my specific borrowing profile and income?`
    }
  })
}
</script>

