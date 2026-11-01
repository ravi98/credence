<template>
  <footer class="bg-[#1E2D39] text-[#F3F5F6] pt-14 pb-10 border-t border-[#3C4D57]/30 text-sm">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="grid grid-cols-1 md:grid-cols-4 gap-8 pb-12 border-b border-white/10">
        <!-- Brand Info -->
        <div class="space-y-3">
          <div class="flex items-center gap-2">
            <div class="w-7 h-7 rounded-md bg-[#2D526E] flex items-center justify-center text-white font-bold text-xs">
              <Landmark class="w-4 h-4" />
            </div>
            <span class="text-lg font-bold text-white">Cred<span class="text-[#91B3C5]">ence</span></span>
          </div>
          <p class="text-xs text-[#B9C4CB] leading-relaxed">
            Find the right loan. Understand every rupee. Strict closed-domain RAG grounded on 163 verified bank schemes and official RBI circulars.
          </p>
          <div class="flex items-center gap-2 text-xs text-[#2F7658] bg-[#EAF0EA] px-2.5 py-1 rounded inline-flex font-medium">
            <ShieldCheck class="w-3.5 h-3.5" />
            <span>Zero Hallucination Guarantee</span>
          </div>
        </div>

        <!-- Loan Categories -->
        <div>
          <h4 class="text-xs font-semibold uppercase tracking-wider text-white mb-3">Loan Categories</h4>
          <ul class="space-y-2 text-xs text-[#B9C4CB]">
            <li><router-link to="/explore?category=Home+Loan" class="hover:text-white transition">Home Loans</router-link></li>
            <li><router-link to="/explore?category=Personal+Loan" class="hover:text-white transition">Personal Loans</router-link></li>
            <li><router-link to="/explore?category=Education+Loan" class="hover:text-white transition">Education Loans (80E)</router-link></li>
            <li><router-link to="/explore?category=Vehicle+Loan" class="hover:text-white transition">Vehicle & Car Loans</router-link></li>
          </ul>
        </div>

        <!-- Decision Tools -->
        <div>
          <h4 class="text-xs font-semibold uppercase tracking-wider text-white mb-3">Decision Tools</h4>
          <ul class="space-y-2 text-xs text-[#B9C4CB]">
            <li><router-link to="/advisor" class="hover:text-white transition">Credence AI Advisor</router-link></li>
            <li><router-link to="/compare" class="hover:text-white transition">Side-by-Side Comparison</router-link></li>
            <li><router-link to="/calculators/emi" class="hover:text-white transition">Deterministic EMI Calculator</router-link></li>
            <li><router-link to="/learn" class="hover:text-white transition">Credence Learn Hub</router-link></li>
          </ul>
        </div>

        <!-- Institutional Trust & Grounding -->
        <div>
          <h4 class="text-xs font-semibold uppercase tracking-wider text-white mb-3">Coverage & Benchmark</h4>
          <p class="text-xs text-[#B9C4CB] leading-relaxed mb-2">
            Coverage across 34 public, private, and NBFC lenders in India. Deterministic calculations for EBLR, MCLR, and Repo-linked floating rates.
          </p>
          <div class="text-[11px] text-[#91B3C5] font-mono">
            Updated October 2026 Verified Catalog
          </div>
        </div>
      </div>

      <!-- Legal & RBI Grounding Disclaimer -->
      <div class="pt-8 text-xs text-[#8A9BA8] leading-relaxed space-y-2">
        <p>
          <strong>Disclaimer:</strong> Credence is an independent AI-powered financial research and comparison platform. We are not a bank, NBFC, or direct lender, nor do we issue loan approvals or solicit deposits. All interest rate ranges, processing fees, benchmark margins (EBLR/MCLR), and eligibility criteria are retrieved directly from published bank filings and RBI notifications. Always verify terms and read the Key Fact Statement (KFS) provided by your selected lender before executing loan agreements.
        </p>
        <div class="flex flex-col sm:flex-row justify-between items-center pt-4 border-t border-white/5 text-[11px] text-[#63727C]">
          <span>© 2026 Credence. Grounded Indian Retail Lending Advisor.</span>
          <div class="flex gap-4 mt-2 sm:mt-0">
            <span>Privacy Policy</span>
            <span>Terms of Service</span>
            <span>Responsible Lending</span>
          </div>
        </div>
      </div>
    </div>
  </footer>
</template>

<script setup>
import { Landmark, ShieldCheck } from 'lucide-vue-next'
</script>

