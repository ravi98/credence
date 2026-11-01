<template>
  <header class="sticky top-0 z-40 bg-surface-canvas/90 backdrop-blur-md border-b border-surface-border">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
      <!-- Logo -->
      <router-link to="/" class="flex items-center gap-2.5 group">
        <div class="w-8 h-8 rounded-lg bg-brand flex items-center justify-center text-white shadow-sm group-hover:bg-brand-hover transition">
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
      <nav class="hidden md:flex items-center gap-7 text-sm font-medium text-brand-deep">
        <router-link 
          to="/explore" 
          class="hover:text-brand transition py-1"
          active-class="text-brand font-semibold border-b-2 border-brand"
        >
          Explore Loans
        </router-link>
        <router-link 
          to="/compare" 
          class="hover:text-brand transition py-1"
          active-class="text-brand font-semibold border-b-2 border-brand"
        >
          Compare
        </router-link>
        <router-link 
          to="/learn" 
          class="hover:text-brand transition py-1"
          active-class="text-brand font-semibold border-b-2 border-brand"
        >
          Learn
        </router-link>
        <router-link 
          to="/calculators/emi" 
          class="hover:text-brand transition py-1"
          active-class="text-brand font-semibold border-b-2 border-brand"
        >
          Calculators
        </router-link>
      </nav>

      <!-- CTA -->
      <div class="hidden md:flex items-center gap-3">
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
      <div class="pt-2">
        <router-link 
          to="/advisor" 
          @click="mobileMenuOpen = false" 
          class="w-full inline-flex items-center justify-center gap-2 bg-brand text-white text-sm font-semibold px-4 py-2.5 rounded-lg"
        >
          <Sparkles class="w-4 h-4 text-sage-light" />
          <span>Check My Eligibility</span>
        </router-link>
      </div>
    </div>
  </header>
</template>

<script setup>
import { ref } from 'vue'
import { Landmark, Sparkles, Menu, X } from 'lucide-vue-next'

const mobileMenuOpen = ref(false)
</script>

