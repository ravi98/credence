<template>
  <header class="sticky top-0 z-40 bg-surface-canvas/90 backdrop-blur-md border-b border-surface-border">
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

      <!-- Desktop Navigation Links -->
      <nav class="hidden md:flex items-center gap-7 text-sm font-medium text-brand-deep h-16">
        <router-link 
          to="/explore" 
          class="hover:text-brand transition py-5 border-b-2 border-transparent"
          active-class="text-brand font-semibold !border-brand"
        >
          Explore Loans
        </router-link>
        <router-link 
          to="/compare" 
          class="hover:text-brand transition py-5 border-b-2 border-transparent"
          active-class="text-brand font-semibold !border-brand"
        >
          Compare
        </router-link>
        <router-link 
          to="/learn" 
          class="hover:text-brand transition py-5 border-b-2 border-transparent"
          active-class="text-brand font-semibold !border-brand"
        >
          Learn
        </router-link>
        <router-link 
          to="/calculators/emi" 
          class="hover:text-brand transition py-5 border-b-2 border-transparent"
          active-class="text-brand font-semibold !border-brand"
        >
          Calculators
        </router-link>
      </nav>

      <!-- CTA & Auth Section -->
      <div class="hidden md:flex items-center gap-3">
        <!-- Sign In Button if not authenticated -->
        <router-link 
          v-if="!auth.isAuthenticated.value"
          to="/login"
          class="text-sm font-semibold text-brand-deep hover:text-brand px-3.5 py-2 rounded-lg hover:bg-surface-secondary transition"
        >
          Sign In
        </router-link>

        <!-- User Profile Dropdown if authenticated -->
        <div v-else class="relative" ref="dropdownRef">
          <button 
            @click="userMenuOpen = !userMenuOpen"
            class="flex items-center gap-2 p-1.5 rounded-xl border border-surface-border hover:border-brand/30 hover:bg-white bg-white/70 transition cursor-pointer"
          >
            <div class="w-7 h-7 rounded-lg bg-brand text-white flex items-center justify-center text-xs font-bold shadow-2xs">
              {{ getUserInitials(auth.user.value?.name) }}
            </div>
            <span class="text-xs font-bold text-brand-deep max-w-[100px] truncate">
              {{ auth.user.value?.name }}
            </span>
            <ChevronDown class="w-3.5 h-3.5 text-brand-muted" />
          </button>

          <!-- User Menu Dropdown -->
          <div 
            v-if="userMenuOpen"
            class="absolute right-0 mt-2 w-56 rounded-2xl bg-white border border-surface-border shadow-lg py-2 z-50 animate-in fade-in duration-150"
          >
            <div class="px-4 py-2 border-b border-surface-border">
              <p class="text-xs font-bold text-brand-deep truncate">{{ auth.user.value?.name }}</p>
              <p class="text-[11px] text-brand-muted truncate">{{ auth.user.value?.email }}</p>
            </div>
            <router-link 
              to="/advisor" 
              @click="userMenuOpen = false"
              class="flex items-center gap-2 px-4 py-2 text-xs font-medium text-brand-deep hover:bg-surface-secondary transition"
            >
              <Sparkles class="w-3.5 h-3.5 text-sage" />
              <span>Loan Advisory Sessions</span>
            </router-link>
            <router-link 
              to="/my-enquiries" 
              @click="userMenuOpen = false"
              class="flex items-center gap-2 px-4 py-2 text-xs font-medium text-brand-deep hover:bg-surface-secondary transition"
            >
              <FileText class="w-3.5 h-3.5 text-brand" />
              <span>My Loan Enquiries</span>
            </router-link>
            <button 
              @click="handleLogout"
              class="w-full flex items-center gap-2 px-4 py-2 text-xs font-semibold text-red-600 hover:bg-red-50 transition text-left cursor-pointer"
            >
              <LogOut class="w-3.5 h-3.5" />
              <span>Sign Out</span>
            </button>
          </div>
        </div>

        <!-- Primary Advisor CTA -->
        <router-link 
          to="/advisor" 
          class="inline-flex items-center gap-2 bg-brand hover:bg-brand-hover text-white text-sm font-semibold px-4 py-2 rounded-lg transition shadow-sm"
        >
          <Sparkles class="w-4 h-4 text-sage-light" />
          <span>Ask Credence Advisor</span>
        </router-link>
      </div>

      <!-- Mobile Hamburger Button -->
      <button 
        @click="mobileMenuOpen = !mobileMenuOpen"
        class="md:hidden p-2 text-brand-deep hover:bg-surface-secondary rounded-lg"
      >
        <Menu v-if="!mobileMenuOpen" class="w-6 h-6" />
        <X v-else class="w-6 h-6" />
      </button>
    </div>

    <!-- Mobile Dropdown Menu -->
    <div v-show="mobileMenuOpen" class="md:hidden border-b border-surface-border bg-white px-4 py-3 space-y-2">
      <router-link 
        to="/explore" 
        @click="mobileMenuOpen = false" 
        class="block px-3 py-2 rounded-md text-sm font-medium text-brand-deep hover:bg-surface-secondary"
      >
        Explore Loans
      </router-link>
      <router-link 
        to="/compare" 
        @click="mobileMenuOpen = false" 
        class="block px-3 py-2 rounded-md text-sm font-medium text-brand-deep hover:bg-surface-secondary"
      >
        Compare
      </router-link>
      <router-link 
        to="/learn" 
        @click="mobileMenuOpen = false" 
        class="block px-3 py-2 rounded-md text-sm font-medium text-brand-deep hover:bg-surface-secondary"
      >
        Learn
      </router-link>
      <router-link 
        to="/calculators/emi" 
        @click="mobileMenuOpen = false" 
        class="block px-3 py-2 rounded-md text-sm font-medium text-brand-deep hover:bg-surface-secondary"
      >
        Calculators
      </router-link>

      <!-- Auth in Mobile Menu -->
      <div class="pt-2 border-t border-surface-border space-y-2">
        <div v-if="auth.isAuthenticated.value" class="px-3 py-2 bg-surface-canvas rounded-xl flex items-center justify-between">
          <div>
            <div class="text-xs font-bold text-brand-deep">{{ auth.user.value?.name }}</div>
            <div class="text-[11px] text-brand-muted">{{ auth.user.value?.email }}</div>
          </div>
          <button 
            @click="handleLogout" 
            class="text-xs text-red-600 font-bold hover:underline"
          >
            Sign Out
          </button>
        </div>
        <router-link 
          v-else
          to="/login"
          @click="mobileMenuOpen = false"
          class="w-full flex items-center justify-center gap-2 border border-surface-border py-2 rounded-lg text-sm font-semibold text-brand-deep hover:bg-surface-secondary"
        >
          <span>Sign In to Credence</span>
        </router-link>

        <router-link 
          to="/advisor" 
          @click="mobileMenuOpen = false" 
          class="w-full inline-flex items-center justify-center gap-2 bg-brand text-white text-sm font-semibold px-4 py-2.5 rounded-lg"
        >
          <Sparkles class="w-4 h-4 text-sage-light" />
          <span>Ask Credence Advisor</span>
        </router-link>
      </div>
    </div>
  </header>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { Landmark, Sparkles, Menu, X, ChevronDown, LogOut, FileText } from 'lucide-vue-next'
import { useAuth } from '../auth.js'

const router = useRouter()
const auth = useAuth()
const mobileMenuOpen = ref(false)
const userMenuOpen = ref(false)
const dropdownRef = ref(null)

const getUserInitials = (name) => {
  if (!name) return 'U'
  const parts = name.trim().split(' ')
  if (parts.length >= 2) {
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
  }
  return name.slice(0, 2).toUpperCase()
}

const handleLogout = () => {
  auth.logout()
  userMenuOpen.value = false
  mobileMenuOpen.value = false
  router.push('/')
}

const handleClickOutside = (e) => {
  if (dropdownRef.value && !dropdownRef.value.contains(e.target)) {
    userMenuOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>
