<template>
  <header class="h-16 border-b border-surface-border bg-white sticky top-0 z-40 px-4 sm:px-6 lg:px-8 flex items-center justify-between">
    <!-- Left: Logo & Nav Links -->
    <div class="flex items-center gap-6 sm:gap-8">
      <router-link to="/dashboard" class="flex items-center gap-2.5">
        <div class="w-8 h-8 rounded-lg bg-brand-deep text-white flex items-center justify-center font-bold text-sm shadow-sm">
          <Briefcase class="w-4 h-4 text-sage-light" />
        </div>
        <div class="flex flex-col">
          <div class="flex items-baseline">
            <span class="text-lg font-extrabold tracking-tight text-brand-deep">Cred</span>
            <span class="text-lg font-extrabold tracking-tight text-brand">ence</span>
            <span class="ml-1 text-xs font-bold uppercase tracking-wider text-brand px-1.5 py-0.2 bg-brand/10 rounded">CRM</span>
          </div>
          <span class="text-[9px] uppercase tracking-wider text-brand-muted -mt-0.5 font-semibold">Sales & Underwriting Portal</span>
        </div>
      </router-link>

      <nav class="hidden md:flex items-center gap-5 text-sm font-semibold text-brand-deep">
        <router-link 
          to="/dashboard" 
          class="hover:text-brand transition py-5 border-b-2 border-transparent"
          active-class="text-brand font-bold !border-brand"
        >
          Dashboard
        </router-link>
        <router-link 
          to="/leads" 
          class="hover:text-brand transition py-5 border-b-2 border-transparent"
          active-class="text-brand font-bold !border-brand"
        >
          Leads Inbox
        </router-link>
      </nav>
    </div>

    <!-- Right: Role Pill & User Menu -->
    <div class="flex items-center gap-3">
      <!-- Role Badge -->
      <span 
        class="hidden sm:inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold border"
        :class="auth.isManager.value ? 'bg-indigo-50 text-indigo-900 border-indigo-200' : 'bg-surface-secondary text-brand-deep border-surface-border'"
      >
        <ShieldCheck class="w-3.5 h-3.5 text-brand" />
        <span>{{ formatRole(auth.user.value?.role) }}</span>
      </span>

      <!-- User Profile & Logout -->
      <div class="flex items-center gap-2 pl-2 border-l border-surface-border">
        <div class="w-8 h-8 rounded-xl bg-brand text-white flex items-center justify-center text-xs font-bold">
          {{ getUserInitials(auth.user.value?.name) }}
        </div>
        <div class="hidden lg:block text-left text-xs">
          <p class="font-bold text-brand-deep truncate max-w-[130px]">{{ auth.user.value?.name }}</p>
          <p class="text-[10px] text-brand-muted truncate max-w-[130px]">{{ auth.user.value?.email }}</p>
        </div>
        <button 
          @click="handleLogout"
          class="p-2 text-brand-muted hover:text-red-600 rounded-lg hover:bg-red-50 transition ml-1 cursor-pointer"
          title="Sign Out"
        >
          <LogOut class="w-4 h-4" />
        </button>
      </div>
    </div>
  </header>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { Briefcase, ShieldCheck, LogOut } from 'lucide-vue-next'
import { useSalesAuth } from '../auth.js'

const router = useRouter()
const auth = useSalesAuth()

const formatRole = (role) => {
  const map = {
    'SALES_EXECUTIVE': 'Sales Executive',
    'SALES_MANAGER': 'Sales Manager',
    'SALES_ADMIN': 'Sales Administrator',
    'SYSTEM_ADMIN': 'System Admin'
  }
  return map[role] || role || 'Sales Officer'
}

const getUserInitials = (name) => {
  if (!name) return 'SO'
  const parts = name.trim().split(' ')
  if (parts.length >= 2) return `${parts[0][0]}${parts[1][0]}`.toUpperCase()
  return name.substring(0, 2).toUpperCase()
}

const handleLogout = () => {
  auth.logout()
  router.push('/login')
}
</script>

