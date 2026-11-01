<template>
  <div class="min-h-screen bg-surface-canvas flex flex-col justify-between selection:bg-brand/10 selection:text-brand">
    <!-- Top Minimalist Navbar (Credible Style) -->
    <header class="border-b border-surface-border bg-white/90 backdrop-blur-md sticky top-0 z-40">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <!-- Logo -->
        <router-link to="/" class="flex items-center gap-2.5 group">
          <div class="w-8 h-8 rounded-lg bg-brand flex items-center justify-center text-white shadow-2xs group-hover:bg-brand-hover transition">
            <Landmark class="w-4 h-4" />
          </div>
          <div class="flex flex-col">
            <div class="flex items-baseline">
              <span class="text-xl font-bold tracking-tight text-brand-deep">Cred</span>
              <span class="text-xl font-bold tracking-tight text-brand">ence</span>
            </div>
            <span class="text-[9px] uppercase tracking-wider text-brand-muted -mt-1 font-medium">Indian Loan Advisor</span>
          </div>
        </router-link>

        <!-- Right Action: Support & Mode Switcher -->
        <div class="flex items-center gap-4 sm:gap-6 text-xs sm:text-sm">
          <div class="hidden md:flex items-center gap-1.5 text-brand-muted font-medium">
            <HelpCircle class="w-4 h-4 text-brand-icon" />
            <span>Have questions?</span>
            <a href="mailto:support@credence.com" class="text-brand font-semibold hover:underline">
              support@credence.com
            </a>
          </div>

          <div class="border-l border-surface-border pl-4 sm:pl-6 text-brand-muted font-medium">
            <span v-if="isLoginMode">Don't have an account?</span>
            <span v-else>Already have an account?</span>
            <button 
              @click="toggleMode" 
              class="ml-1.5 font-bold text-brand hover:text-brand-hover hover:underline transition cursor-pointer"
            >
              {{ isLoginMode ? 'Sign up' : 'Sign in' }}
            </button>
          </div>
        </div>
      </div>
    </header>

    <!-- Main Content Area: Credible 2-Column Desktop / Responsive Stack -->
    <main class="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12 flex items-center">
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-14 items-center w-full">
        
        <!-- Left Column: Credible Value Pillars & Trust Signals (Desktop Featured) -->
        <div class="lg:col-span-6 xl:col-span-7 space-y-6 lg:pr-4">
          <!-- Trust Pill -->
          <div class="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-surface-light border border-brand/20 text-xs font-bold text-brand">
            <ShieldCheck class="w-3.5 h-3.5 text-sage" />
            <span>Trusted by 12,000+ Borrowers Across India</span>
          </div>

          <!-- Main Value Headline -->
          <div class="space-y-3">
            <h1 class="text-3xl sm:text-4xl lg:text-5xl font-bold text-brand-deep tracking-tight leading-tight">
              The smarter way to find your <span class="text-brand">ideal loan.</span>
            </h1>
            <p class="text-sm sm:text-base text-brand-muted font-medium leading-relaxed max-w-xl">
              Compare 163+ verified lending schemes from 34 scheduled Indian banks. Transparent interest rates, official RBI benchmark spreads, and zero phone spam.
            </p>
          </div>

          <!-- Credible Value Checklist -->
          <div class="space-y-3.5 pt-2">
            <div class="flex items-start gap-3">
              <div class="w-5 h-5 rounded-full bg-sage-light text-sage flex items-center justify-center flex-shrink-0 mt-0.5 border border-sage-border">
                <Check class="w-3.5 h-3.5" />
              </div>
              <div>
                <p class="text-xs sm:text-sm font-bold text-brand-deep">Checking rates won't hurt your credit score</p>
                <p class="text-[11px] sm:text-xs text-brand-muted">Explore prequalified rate estimates and benchmark spreads without triggering a hard credit inquiry.</p>
              </div>
            </div>

            <div class="flex items-start gap-3">
              <div class="w-5 h-5 rounded-full bg-sage-light text-sage flex items-center justify-center flex-shrink-0 mt-0.5 border border-sage-border">
                <Check class="w-3.5 h-3.5" />
              </div>
              <div>
                <p class="text-xs sm:text-sm font-bold text-brand-deep">Compare 34+ banks in under 2 minutes</p>
                <p class="text-[11px] sm:text-xs text-brand-muted">SBI, HDFC Bank, ICICI Bank, Axis Bank, Bank of Baroda, and Punjab National Bank benchmarked side-by-side.</p>
              </div>
            </div>

            <div class="flex items-start gap-3">
              <div class="w-5 h-5 rounded-full bg-sage-light text-sage flex items-center justify-center flex-shrink-0 mt-0.5 border border-sage-border">
                <Check class="w-3.5 h-3.5" />
              </div>
              <div>
                <p class="text-xs sm:text-sm font-bold text-brand-deep">100% free with zero telemarketer spam</p>
                <p class="text-[11px] sm:text-xs text-brand-muted">We never sell your phone number to third-party telemarketers or aggressive commission agents.</p>
              </div>
            </div>
          </div>

          <!-- Featured Partner Banks Pill Grid -->
          <div class="pt-2">
            <p class="text-[11px] font-bold uppercase tracking-wider text-brand-muted mb-2.5">
              Verified Lending Benchmarks
            </p>
            <div class="flex flex-wrap gap-2">
              <span class="px-3 py-1.5 rounded-lg bg-white border border-surface-border text-xs font-semibold text-brand-deep shadow-2xs">
                State Bank of India
              </span>
              <span class="px-3 py-1.5 rounded-lg bg-white border border-surface-border text-xs font-semibold text-brand-deep shadow-2xs">
                HDFC Bank
              </span>
              <span class="px-3 py-1.5 rounded-lg bg-white border border-surface-border text-xs font-semibold text-brand-deep shadow-2xs">
                ICICI Bank
              </span>
              <span class="px-3 py-1.5 rounded-lg bg-white border border-surface-border text-xs font-semibold text-brand-deep shadow-2xs">
                Axis Bank
              </span>
              <span class="px-3 py-1.5 rounded-lg bg-white border border-surface-border text-xs font-semibold text-brand-deep shadow-2xs">
                Bank of Baroda
              </span>
              <span class="px-3 py-1.5 rounded-lg bg-white border border-surface-border text-xs font-semibold text-brand-deep shadow-2xs">
                Federal Bank
              </span>
            </div>
          </div>

          <!-- Trustpilot / User Testimonial Snippet -->
          <div class="p-4 rounded-xl bg-white border border-surface-border shadow-2xs hidden sm:block">
            <div class="flex items-center gap-1 text-amber-500 mb-1.5">
              <Star class="w-4 h-4 fill-amber-400 text-amber-400" />
              <Star class="w-4 h-4 fill-amber-400 text-amber-400" />
              <Star class="w-4 h-4 fill-amber-400 text-amber-400" />
              <Star class="w-4 h-4 fill-amber-400 text-amber-400" />
              <Star class="w-4 h-4 fill-amber-400 text-amber-400" />
              <span class="text-xs font-bold text-brand-deep ml-1.5">4.8 / 5 Rating</span>
              <span class="text-xs text-brand-muted">· 10,000+ Reviews</span>
            </div>
            <p class="text-xs text-brand-deep italic leading-relaxed">
              "Credence made evaluating EBLR reset frequencies and processing fee caps completely straightforward. Found a home loan rate 0.45% lower than my relationship manager offered."
            </p>
            <p class="text-[11px] font-semibold text-brand-muted mt-1.5">
              — Vikram S., Homeowner in Bengaluru
            </p>
          </div>
        </div>

        <!-- Right Column: Authentication Card (Credible Structure) -->
        <div class="lg:col-span-6 xl:col-span-5 flex justify-center">
          <div class="w-full max-w-md bg-white rounded-2xl border border-surface-border shadow-sm p-6 sm:p-8">
            
            <!-- Auth Mode Switcher Tabs -->
            <div class="flex rounded-xl bg-surface-canvas p-1 border border-surface-border mb-6">
              <button 
                type="button"
                @click="isLoginMode = true"
                class="flex-1 py-2 text-xs sm:text-sm font-bold rounded-lg transition text-center cursor-pointer"
                :class="isLoginMode ? 'bg-white text-brand shadow-2xs' : 'text-brand-muted hover:text-brand-deep'"
              >
                Sign In
              </button>
              <button 
                type="button"
                @click="isLoginMode = false"
                class="flex-1 py-2 text-xs sm:text-sm font-bold rounded-lg transition text-center cursor-pointer"
                :class="!isLoginMode ? 'bg-white text-brand shadow-2xs' : 'text-brand-muted hover:text-brand-deep'"
              >
                Create Account
              </button>
            </div>

            <!-- Card Headline & Instructions -->
            <div class="mb-5">
              <h2 class="text-xl sm:text-2xl font-bold text-brand-deep tracking-tight">
                {{ isLoginMode ? 'Welcome back' : 'Create your Credence account' }}
              </h2>
              <p class="text-xs text-brand-muted font-medium mt-1">
                {{ isLoginMode ? 'Sign in to access your saved loans, rate alerts, and personalized comparisons.' : 'Start comparing verified bank schemes with unbiased closed-domain intelligence.' }}
              </p>
            </div>

            <!-- Error Banner -->
            <div 
              v-if="errorMessage" 
              class="mb-4 p-3 rounded-xl bg-red-50 border border-red-200 text-red-700 text-xs flex items-start gap-2.5 animate-in fade-in duration-150"
            >
              <AlertCircle class="w-4 h-4 flex-shrink-0 mt-0.5 text-red-600" />
              <span class="font-medium break-words">{{ errorMessage }}</span>
            </div>

            <!-- Success Banner -->
            <div 
              v-if="successMessage" 
              class="mb-4 p-3 rounded-xl bg-sage-light/60 border border-sage-border text-sage text-xs flex items-start gap-2.5 animate-in fade-in duration-150"
            >
              <CheckCircle2 class="w-4 h-4 flex-shrink-0 mt-0.5 text-sage" />
              <span class="font-medium break-words">{{ successMessage }}</span>
            </div>

            <!-- Google Sign-in Section (Production Standard) -->
            <div class="relative w-full">
              <!-- Official Google Identity Button Mount Target -->
              <div v-show="googleBtnMounted" ref="googleBtnRef" class="w-full flex justify-center min-h-[44px]"></div>

              <!-- Sleek Credible-Style Google Button (when GIS button is loading or on click fallback) -->
              <button 
                v-if="!googleBtnMounted"
                type="button" 
                @click="handleGoogleSignInClick"
                :disabled="loading"
                class="w-full flex items-center justify-center gap-3 py-2.5 sm:py-3 px-4 rounded-xl border border-surface-border bg-white hover:bg-surface-secondary text-brand-deep font-semibold text-xs sm:text-sm transition shadow-2xs hover:shadow-xs disabled:opacity-50 cursor-pointer"
              >
                <!-- Google Multi-Color SVG G Icon -->
                <svg class="w-5 h-5 flex-shrink-0" viewBox="0 0 24 24">
                  <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                  <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                  <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z" />
                  <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z" />
                </svg>
                <span>Continue with Google</span>
              </button>
            </div>

            <!-- Divider -->
            <div class="relative my-5 text-center">
              <div class="absolute inset-0 flex items-center">
                <div class="w-full border-t border-surface-border"></div>
              </div>
              <span class="relative bg-white px-3 text-[11px] uppercase tracking-wider text-brand-muted font-bold">
                or continue with email
              </span>
            </div>

            <!-- Email & Password Form -->
            <form @submit.prevent="handleSubmit" class="space-y-3.5">
              <!-- Full Name (Only on Registration) -->
              <div v-if="!isLoginMode">
                <label for="name" class="block text-[11px] font-bold uppercase tracking-wider text-brand-muted mb-1">
                  Full Name
                </label>
                <div class="relative">
                  <input 
                    id="name" 
                    v-model="name" 
                    type="text" 
                    required 
                    placeholder="e.g. Arjun Sharma"
                    class="w-full pl-9 pr-3.5 py-2.5 rounded-xl border border-surface-border focus:border-brand focus:ring-2 focus:ring-brand/20 text-xs sm:text-sm font-medium text-brand-deep placeholder-brand-muted/60 transition outline-none"
                  />
                  <User class="w-4 h-4 text-brand-muted absolute left-3 top-3" />
                </div>
              </div>

              <!-- Email Address -->
              <div>
                <label for="email" class="block text-[11px] font-bold uppercase tracking-wider text-brand-muted mb-1">
                  Email Address
                </label>
                <div class="relative">
                  <input 
                    id="email" 
                    v-model="email" 
                    type="email" 
                    required 
                    autocomplete="email"
                    placeholder="name@example.com"
                    class="w-full pl-9 pr-3.5 py-2.5 rounded-xl border border-surface-border focus:border-brand focus:ring-2 focus:ring-brand/20 text-xs sm:text-sm font-medium text-brand-deep placeholder-brand-muted/60 transition outline-none"
                  />
                  <Mail class="w-4 h-4 text-brand-muted absolute left-3 top-3" />
                </div>
              </div>

              <!-- Password -->
              <div>
                <div class="flex items-center justify-between mb-1">
                  <label for="password" class="block text-[11px] font-bold uppercase tracking-wider text-brand-muted">
                    Password
                  </label>
                  <button 
                    v-if="isLoginMode" 
                    type="button" 
                    @click="forgotPasswordModal = true"
                    class="text-xs font-semibold text-brand hover:text-brand-hover hover:underline cursor-pointer"
                  >
                    Forgot password?
                  </button>
                </div>
                <div class="relative">
                  <input 
                    id="password" 
                    v-model="password" 
                    :type="showPassword ? 'text' : 'password'" 
                    required 
                    autocomplete="current-password"
                    placeholder="••••••••"
                    class="w-full pl-9 pr-10 py-2.5 rounded-xl border border-surface-border focus:border-brand focus:ring-2 focus:ring-brand/20 text-xs sm:text-sm font-medium text-brand-deep placeholder-brand-muted/60 transition outline-none"
                  />
                  <Lock class="w-4 h-4 text-brand-muted absolute left-3 top-3" />
                  <button 
                    type="button" 
                    @click="showPassword = !showPassword"
                    class="absolute right-3 top-2.5 p-0.5 text-brand-muted hover:text-brand-deep transition cursor-pointer"
                    tabindex="-1"
                  >
                    <EyeOff v-if="showPassword" class="w-4 h-4" />
                    <Eye v-else class="w-4 h-4" />
                  </button>
                </div>
                <p v-if="!isLoginMode" class="text-[11px] text-brand-muted mt-1 font-medium">
                  Must be at least 6 characters.
                </p>
              </div>

              <!-- Remember Me Checkbox -->
              <div v-if="isLoginMode" class="flex items-center">
                <input 
                  id="remember" 
                  v-model="rememberMe" 
                  type="checkbox"
                  class="w-4 h-4 rounded text-brand border-surface-border focus:ring-brand/30 cursor-pointer"
                />
                <label for="remember" class="ml-2 text-xs font-medium text-brand-deep select-none cursor-pointer">
                  Remember this device for 14 days
                </label>
              </div>

              <!-- Primary Submit Button -->
              <button 
                type="submit" 
                :disabled="loading"
                class="w-full flex items-center justify-center gap-2 py-3 px-4 rounded-xl text-white bg-brand hover:bg-brand-hover text-sm font-bold shadow-sm transition disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer mt-1"
              >
                <Loader2 v-if="loading" class="w-4 h-4 animate-spin" />
                <span>{{ isLoginMode ? 'Sign In' : 'Create Free Account' }}</span>
              </button>
            </form>

            <!-- Credible Inline Legal Agreement Microcopy -->
            <div class="mt-5 pt-4 border-t border-surface-border text-[11px] text-brand-muted text-center leading-relaxed">
              <span>By clicking Continue with Google or {{ isLoginMode ? 'Sign In' : 'Create Free Account' }}, you agree to Credence's </span>
              <button @click="openLegalModal('terms')" class="text-brand font-semibold hover:underline">Terms of Use</button>, 
              <button @click="openLegalModal('privacy')" class="text-brand font-semibold hover:underline">Privacy Policy</button>, and 
              <button @click="openLegalModal('electronic')" class="text-brand font-semibold hover:underline">Electronic Disclosure Policy</button>.
            </div>

            <!-- Bot & Encryption Subtext -->
            <div class="mt-3 text-[10px] text-brand-muted/80 text-center flex items-center justify-center gap-2">
              <span class="flex items-center gap-1">
                <Lock class="w-3 h-3 text-sage" />
                256-Bit SSL Bank Encryption
              </span>
              <span>·</span>
              <span>Anti-Fraud Protected</span>
            </div>
          </div>
        </div>

      </div>
    </main>

    <!-- Credible Regulatory Footer & Legal Disclosures -->
    <footer class="border-t border-surface-border bg-white mt-8 py-8">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-6">
        
        <!-- Credible Mandatory Regulatory Notice -->
        <div class="text-[11px] text-brand-muted leading-relaxed space-y-2 border-b border-surface-border pb-6">
          <p>
            <strong>Advisory Disclosure:</strong> Credence is an independent loan comparison and advisory platform, not a direct lender, banking correspondent, or credit institution. Credence does not approve loans, issue credit sanctions, or collect fees from borrowers for comparing interest rates.
          </p>
          <p>
            Prequalified rate ranges and APR calculations presented across 34 scheduled commercial banks are based on publicly verified external benchmark lending rates (RBI Repo Linked Lending Rate / MCLR) and bank-reported spread schedules. Actual loan sanction amounts, margin requirements, interest spreads, and processing fees are determined solely by the respective bank upon full document submission and credit underwriting evaluation.
          </p>
        </div>

        <!-- Footer Navigation Links -->
        <div class="flex flex-wrap items-center justify-between gap-4 text-xs text-brand-muted font-medium">
          <div class="flex flex-wrap items-center gap-4 sm:gap-6">
            <button @click="openLegalModal('terms')" class="hover:text-brand transition cursor-pointer">
              Terms of Use
            </button>
            <button @click="openLegalModal('privacy')" class="hover:text-brand transition cursor-pointer">
              Privacy Policy
            </button>
            <button @click="openLegalModal('electronic')" class="hover:text-brand transition cursor-pointer">
              Electronic Disclosures
            </button>
            <button @click="openLegalModal('security')" class="hover:text-brand transition cursor-pointer">
              Security & Encryption
            </button>
            <a href="mailto:support@credence.com" class="hover:text-brand transition">
              Customer Support
            </a>
          </div>

          <div class="text-[11px] text-brand-muted">
            © 2026 Credence Financial Technologies Inc. All rights reserved.
          </div>
        </div>
      </div>
    </footer>

    <!-- Interactive Legal Disclosures Modal (Terms / Privacy / Electronic Policy) -->
    <div 
      v-if="legalModalOpen" 
      class="fixed inset-0 z-50 bg-brand-deep/50 backdrop-blur-2xs flex items-center justify-center p-4 animate-in fade-in duration-150"
    >
      <div class="bg-white rounded-2xl max-w-lg w-full max-h-[85vh] flex flex-col border border-surface-border shadow-xl">
        <div class="p-5 border-b border-surface-border flex items-center justify-between">
          <div class="flex items-center gap-2.5">
            <div class="w-8 h-8 rounded-lg bg-surface-light text-brand flex items-center justify-center">
              <FileText class="w-4 h-4" />
            </div>
            <h3 class="text-base font-bold text-brand-deep">{{ legalModalTitle }}</h3>
          </div>
          <button 
            @click="legalModalOpen = false" 
            class="text-brand-muted hover:text-brand-deep p-1.5 rounded-lg hover:bg-surface-secondary transition cursor-pointer"
          >
            <X class="w-5 h-5" />
          </button>
        </div>

        <div class="p-6 overflow-y-auto space-y-4 text-xs sm:text-sm text-brand-deep/90 leading-relaxed">
          <div v-html="legalModalBody"></div>
        </div>

        <div class="p-4 border-t border-surface-border bg-surface-canvas rounded-b-2xl flex justify-end">
          <button 
            @click="legalModalOpen = false" 
            class="px-5 py-2.5 rounded-xl bg-brand hover:bg-brand-hover text-white text-xs font-bold transition cursor-pointer"
          >
            I Understand
          </button>
        </div>
      </div>
    </div>

    <!-- Production Password Recovery Modal -->
    <div 
      v-if="forgotPasswordModal" 
      class="fixed inset-0 z-50 bg-brand-deep/50 backdrop-blur-2xs flex items-center justify-center p-4 animate-in fade-in duration-150"
    >
      <div class="bg-white rounded-2xl max-w-md w-full p-6 border border-surface-border shadow-lg space-y-4">
        <div class="flex items-start justify-between">
          <div class="flex items-center gap-2.5">
            <div class="w-8 h-8 rounded-lg bg-surface-light text-brand flex items-center justify-center">
              <KeyRound class="w-4 h-4" />
            </div>
            <h3 class="text-base font-bold text-brand-deep">Reset your password</h3>
          </div>
          <button 
            @click="forgotPasswordModal = false" 
            class="text-brand-muted hover:text-brand-deep p-1 rounded-lg hover:bg-surface-secondary transition cursor-pointer"
          >
            <X class="w-5 h-5" />
          </button>
        </div>

        <div v-if="resetSent" class="p-4 rounded-xl bg-sage-light/60 border border-sage-border text-sage text-xs leading-relaxed space-y-2">
          <p class="font-bold">Check your inbox</p>
          <p>If an account exists for <span class="font-semibold">{{ resetEmail }}</span>, instructions to reset your password have been sent.</p>
        </div>

        <form v-else @submit.prevent="handlePasswordReset" class="space-y-3.5">
          <p class="text-xs text-brand-muted leading-relaxed">
            Enter the email address associated with your Credence account and we'll send you a secure link to reset your password.
          </p>
          <div>
            <label class="block text-[11px] font-bold uppercase tracking-wider text-brand-muted mb-1">
              Email Address
            </label>
            <input 
              v-model="resetEmail" 
              type="email" 
              required 
              placeholder="name@example.com"
              class="w-full px-3.5 py-2.5 rounded-xl border border-surface-border focus:border-brand focus:ring-2 focus:ring-brand/20 text-xs sm:text-sm font-medium text-brand-deep outline-none"
            />
          </div>
          <button 
            type="submit" 
            class="w-full py-2.5 rounded-xl bg-brand hover:bg-brand-hover text-white text-xs font-bold transition cursor-pointer"
          >
            Send Reset Link
          </button>
        </form>

        <div class="pt-2 border-t border-surface-border text-center">
          <button 
            @click="forgotPasswordModal = false" 
            class="text-xs font-bold text-brand hover:underline cursor-pointer"
          >
            Back to Sign In
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { 
  Landmark, 
  Mail, 
  Lock, 
  User, 
  Eye, 
  EyeOff, 
  ShieldCheck, 
  AlertCircle, 
  CheckCircle2, 
  Loader2, 
  KeyRound, 
  X, 
  Check,
  Star,
  HelpCircle,
  FileText
} from 'lucide-vue-next'
import { useAuth } from '../auth.js'

const router = useRouter()
const route = useRoute()
const auth = useAuth()

const isLoginMode = ref(true)
const name = ref('')
const email = ref('')
const password = ref('')
const showPassword = ref(false)
const rememberMe = ref(true)
const loading = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
const forgotPasswordModal = ref(false)
const resetEmail = ref('')
const resetSent = ref(false)

// Google OAuth State
const googleClientId = ref('')
const googleBtnRef = ref(null)
const googleBtnMounted = ref(false)

const legalModalOpen = ref(false)
const legalModalTitle = ref('')
const legalModalBody = ref('')

const toggleMode = () => {
  isLoginMode.value = !isLoginMode.value
  errorMessage.value = ''
  successMessage.value = ''
}

// Fetch Google OAuth configuration from backend developer environment
const loadGoogleConfig = async () => {
  try {
    const res = await fetch('/api/auth/google/config')
    if (res.ok) {
      const data = await res.json()
      googleClientId.value = data.google_client_id || ''
      if (googleClientId.value) {
        setupGoogleIdentityServices()
      }
    }
  } catch (err) {
    console.warn('Failed to load Google OAuth config:', err)
  }
}

// Initialize official Google Identity Services
const setupGoogleIdentityServices = (attempt = 0) => {
  if (!window.google?.accounts?.id) {
    if (attempt < 15) {
      setTimeout(() => setupGoogleIdentityServices(attempt + 1), 250)
    }
    return
  }

  try {
    window.google.accounts.id.initialize({
      client_id: googleClientId.value,
      callback: handleRealGoogleCredential,
      auto_select: false,
      cancel_on_tap_outside: true
    })

    if (googleBtnRef.value) {
      googleBtnRef.value.innerHTML = ''
      window.google.accounts.id.renderButton(googleBtnRef.value, {
        type: 'standard',
        theme: 'outline',
        size: 'large',
        text: 'continue_with',
        shape: 'rectangular',
        logo_alignment: 'left',
        width: 380
      })
      googleBtnMounted.value = true
    }
  } catch (err) {
    console.error('Google Identity Services initialization error:', err)
  }
}

// User-facing click handler when fallback button is clicked
const handleGoogleSignInClick = () => {
  if (googleClientId.value && window.google?.accounts?.id) {
    window.google.accounts.id.prompt()
  } else {
    errorMessage.value = 'Google sign-in is currently unavailable. Please sign in with your email address.'
  }
}

// Handle real Google credential returned by Google accounts popup
const handleRealGoogleCredential = async (response) => {
  if (!response?.credential) {
    errorMessage.value = 'No credential received from Google.'
    return
  }
  loading.value = true
  errorMessage.value = ''
  try {
    await auth.loginWithGoogle(response.credential)
    successMessage.value = 'Successfully signed in with Google!'
    setTimeout(() => {
      const redirectPath = route.query.redirect || '/advisor'
      router.push(redirectPath)
    }, 400)
  } catch (err) {
    errorMessage.value = err.message || 'Google authentication failed.'
  } finally {
    loading.value = false
  }
}

const handleSubmit = async () => {
  errorMessage.value = ''
  successMessage.value = ''
  loading.value = true

  try {
    if (isLoginMode.value) {
      await auth.login(email.value, password.value)
      const redirectPath = route.query.redirect || '/advisor'
      router.push(redirectPath)
    } else {
      await auth.register(name.value, email.value, password.value)
      successMessage.value = 'Account created successfully! Redirecting...'
      setTimeout(() => {
        const redirectPath = route.query.redirect || '/advisor'
        router.push(redirectPath)
      }, 700)
    }
  } catch (err) {
    errorMessage.value = err.message || 'An error occurred. Please try again.'
  } finally {
    loading.value = false
  }
}

const handlePasswordReset = () => {
  if (!resetEmail.value) return
  resetSent.value = true
}

const openLegalModal = (type) => {
  if (type === 'terms') {
    legalModalTitle.value = 'Credence Terms of Use'
    legalModalBody.value = `
      <p class="mb-3"><strong>1. Scope of Advisory Services:</strong> Credence provides comparative lending analysis using deterministic data from Reserve Bank of India (RBI) scheduled commercial banks. Credence is not a lender, broker, or depository institution.</p>
      <p class="mb-3"><strong>2. Rate Validity:</strong> Interest rates, processing fees, and external benchmark lending rates (EBLR) fluctuate according to RBI monetary policy changes. Lenders reserve the right to determine final margin spreads based on individual underwriting criteria.</p>
      <p><strong>3. User Commitments:</strong> Users agree to provide truthful self-declared employment and income parameters when utilizing the Credence Loan Advisor.</p>
    `
  } else if (type === 'privacy') {
    legalModalTitle.value = 'Credence Privacy Policy'
    legalModalBody.value = `
      <p class="mb-3"><strong>1. Zero Spam Commitment:</strong> We never sell, rent, or lease your phone number or email address to aggressive telemarketing lead generators or third-party call centers.</p>
      <p class="mb-3"><strong>2. Bank-Grade Encryption:</strong> All session records and profile credentials are encrypted at rest using industry-standard bcrypt and TLS 1.3 / 256-bit AES in transit.</p>
      <p><strong>3. Data Retention:</strong> You may request complete erasure of your advisory session logs and user account at any time.</p>
    `
  } else if (type === 'electronic') {
    legalModalTitle.value = 'Electronic Disclosure Policy (E-SIGN)'
    legalModalBody.value = `
      <p class="mb-3"><strong>1. Consent to Electronic Notices:</strong> By creating an account or logging in, you consent to receive loan comparison reports, benchmark rate change notifications, and regulatory disclosures electronically.</p>
      <p><strong>2. Hardware & Software Requirements:</strong> To access and retain electronic disclosures, you need a modern web browser supporting standard 256-bit SSL encryption.</p>
    `
  } else if (type === 'security') {
    legalModalTitle.value = 'Security & Encryption Standards'
    legalModalBody.value = `
      <p class="mb-3"><strong>1. Cryptographic Protection:</strong> User passwords are encrypted with bcrypt (salt rounds = 12). Tokens are signed with JSON Web Tokens (JWT) using HMAC-SHA256.</p>
      <p class="mb-3"><strong>2. Closed-Domain Grounding:</strong> The Credence Advisory Engine enforces zero-hallucination guardrails by citing verified institutional banking rate sheets.</p>
      <p><strong>3. Anti-Scraping & Rate Limiting:</strong> Endpoints are monitored to prevent automated credential stuffing and malicious bot attacks.</p>
    `
  }
  legalModalOpen.value = true
}

onMounted(() => {
  loadGoogleConfig()
})
</script>
