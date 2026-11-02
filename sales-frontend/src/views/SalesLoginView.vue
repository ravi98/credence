<template>
  <div class="min-h-screen bg-surface-canvas flex flex-col justify-center py-12 sm:px-6 lg:px-8">
    <div class="sm:mx-auto sm:w-full sm:max-w-md text-center">
      <div class="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-brand-deep text-white shadow-md mb-4">
        <Briefcase class="w-6 h-6 text-sage-light" />
      </div>
      <h2 class="text-2xl sm:text-3xl font-extrabold tracking-tight text-brand-deep">
        Credence Sales CRM
      </h2>
      <p class="mt-1.5 text-xs sm:text-sm text-brand-muted font-medium">
        Operations, Underwriting & Lender Coordination Portal
      </p>
    </div>

    <div class="mt-8 sm:mx-auto sm:w-full sm:max-w-md px-4 sm:px-0">
      <div class="bg-white py-8 px-6 sm:px-10 shadow-lg rounded-3xl border border-surface-border space-y-6">
        <!-- Error Alert -->
        <div v-if="errorMessage" class="p-3.5 rounded-xl bg-red-50 border border-red-200 text-red-800 text-xs sm:text-sm font-medium flex items-center gap-2">
          <AlertCircle class="w-4 h-4 flex-shrink-0 text-red-600" />
          <span>{{ errorMessage }}</span>
        </div>

        <form @submit.prevent="handleLogin" class="space-y-4">
          <div>
            <label class="block text-xs font-bold text-brand-deep mb-1">Work Email</label>
            <input 
              v-model="email"
              type="email" 
              required
              placeholder="officer@credence.in"
              class="w-full text-xs sm:text-sm px-3.5 py-2.5 rounded-xl border border-surface-border focus:border-brand focus:ring-1 focus:ring-brand outline-none"
            />
          </div>

          <div>
            <label class="block text-xs font-bold text-brand-deep mb-1">Password</label>
            <input 
              v-model="password"
              type="password" 
              required
              placeholder="••••••••"
              class="w-full text-xs sm:text-sm px-3.5 py-2.5 rounded-xl border border-surface-border focus:border-brand focus:ring-1 focus:ring-brand outline-none"
            />
          </div>

          <button
            type="submit"
            :disabled="isLoading"
            class="w-full py-2.5 px-4 rounded-xl bg-brand hover:bg-brand-hover text-white text-xs sm:text-sm font-bold shadow-sm transition disabled:opacity-50 flex items-center justify-center gap-2 cursor-pointer"
          >
            <Loader2 v-if="isLoading" class="w-4 h-4 animate-spin" />
            <span>{{ isLoading ? 'Signing In...' : 'Sign In to CRM' }}</span>
          </button>
        </form>

        <!-- Quick Demo Switcher -->
        <div class="pt-4 border-t border-surface-border space-y-2.5">
          <span class="text-[11px] uppercase font-bold tracking-wider text-brand-muted block text-center">
            One-Click Role Demonstration
          </span>
          <div class="grid grid-cols-2 gap-2">
            <button
              @click="demoLogin('exec_test@credence.in', 'password123')"
              type="button"
              class="p-2.5 rounded-xl border border-surface-border hover:border-brand/40 bg-surface-canvas hover:bg-white text-left transition cursor-pointer"
            >
              <strong class="block text-xs font-bold text-brand-deep">Sales Executive</strong>
              <span class="text-[10px] text-brand-muted">Assigned leads only</span>
            </button>
            <button
              @click="demoLogin('manager_test@credence.in', 'password123')"
              type="button"
              class="p-2.5 rounded-xl border border-surface-border hover:border-brand/40 bg-surface-canvas hover:bg-white text-left transition cursor-pointer"
            >
              <strong class="block text-xs font-bold text-brand-deep">Sales Manager</strong>
              <span class="text-[10px] text-brand-muted">Team scope & assignment</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { Briefcase, AlertCircle, Loader2 } from 'lucide-vue-next'
import { useSalesAuth } from '../auth.js'

const router = useRouter()
const auth = useSalesAuth()

const email = ref('')
const password = ref('')
const isLoading = ref(false)
const errorMessage = ref('')

const handleLogin = async () => {
  if (!email.value || !password.value) return
  isLoading.value = true
  errorMessage.value = ''

  try {
    await auth.login(email.value.trim(), password.value)
    router.push('/dashboard')
  } catch (err) {
    errorMessage.value = err.message || 'Invalid credentials or non-sales account.'
  } finally {
    isLoading.value = false
  }
}

const demoLogin = async (demoEmail, demoPwd) => {
  email.value = demoEmail
  password.value = demoPwd
  await handleLogin()
}
</script>

