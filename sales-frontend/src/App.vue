<template>
  <div class="min-h-screen bg-surface-canvas text-brand-deep">
    <router-view />
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useSalesAuth } from './auth.js'

const auth = useSalesAuth()

onMounted(async () => {
  await auth.checkAuth()
})
</script>

