<template>
  <div v-if="isOpen" class="fixed inset-0 z-50 overflow-y-auto bg-black/60 backdrop-blur-xs flex items-center justify-center p-3 sm:p-4">
    <div class="relative w-full max-w-md bg-white rounded-3xl shadow-2xl border border-surface-border overflow-hidden">
      <!-- Header -->
      <div class="px-6 py-4.5 border-b border-surface-border flex items-center justify-between bg-surface-canvas/60">
        <div>
          <h3 class="font-bold text-base text-brand-deep">Assign Lead</h3>
          <p class="text-xs text-brand-muted">Lead Reference: {{ leadReference }}</p>
        </div>
        <button 
          @click="close"
          class="p-2 text-brand-muted hover:text-brand-deep rounded-xl hover:bg-surface-secondary cursor-pointer"
        >
          <X class="w-5 h-5" />
        </button>
      </div>

      <!-- Body -->
      <div class="p-6 space-y-4">
        <div v-if="errorMessage" class="p-3 rounded-xl bg-red-50 text-red-800 text-xs font-semibold">
          {{ errorMessage }}
        </div>

        <div>
          <label class="block text-xs font-bold text-brand-deep mb-1.5">
            Select Sales Specialist *
          </label>
          <select 
            v-model="selectedUserId"
            class="w-full text-xs sm:text-sm px-3.5 py-2.5 rounded-xl border border-surface-border bg-white outline-none focus:border-brand"
          >
            <option value="" disabled>-- Select an Executive --</option>
            <option 
              v-for="member in teamMembers" 
              :key="member.id" 
              :value="member.id"
            >
              {{ member.name }} ({{ member.active_leads }} active leads)
            </option>
          </select>
        </div>

        <div>
          <label class="block text-xs font-bold text-brand-deep mb-1.5">
            Assignment Reason / Instructions
          </label>
          <textarea 
            v-model="assignmentReason"
            rows="2"
            placeholder="e.g. Assigned based on high CIBIL and home loan priority in Bengaluru."
            class="w-full text-xs sm:text-sm p-3 rounded-xl border border-surface-border outline-none focus:border-brand"
          ></textarea>
        </div>
      </div>

      <!-- Footer -->
      <div class="px-6 py-4 border-t border-surface-border bg-surface-canvas/60 flex items-center justify-between">
        <button 
          @click="close"
          class="text-xs font-semibold text-brand-muted hover:text-brand-deep px-3 py-2 cursor-pointer"
        >
          Cancel
        </button>
        <button 
          @click="confirmAssignment"
          :disabled="isSubmitting || !selectedUserId"
          class="px-5 py-2.5 rounded-xl bg-brand text-white text-xs font-bold shadow-sm hover:bg-brand-hover disabled:opacity-50 transition cursor-pointer"
        >
          <span>{{ isSubmitting ? 'Assigning...' : 'Confirm Assignment' }}</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { X } from 'lucide-vue-next'

const props = defineProps({
  isOpen: Boolean,
  leadId: String,
  leadReference: String
})

const emit = defineEmits(['close', 'assigned'])

const teamMembers = ref([])
const selectedUserId = ref('')
const assignmentReason = ref('')
const isSubmitting = ref(false)
const errorMessage = ref('')

const fetchTeam = async () => {
  try {
    const token = localStorage.getItem('credence_sales_token')
    const res = await fetch('/api/sales/team', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    if (res.ok) {
      const data = await res.json()
      teamMembers.value = data.team_members || []
      if (teamMembers.value.length > 0) {
        selectedUserId.value = teamMembers.value[0].id
      }
    }
  } catch (err) {
    console.error('Failed to load team members:', err)
  }
}

watch(() => props.isOpen, (open) => {
  if (open) {
    errorMessage.value = ''
    fetchTeam()
  }
})

const confirmAssignment = async () => {
  if (!selectedUserId.value || isSubmitting.value) return
  isSubmitting.value = true
  errorMessage.value = ''

  try {
    const token = localStorage.getItem('credence_sales_token')
    const res = await fetch(`/api/sales/leads/${props.leadId}/assign`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        assigned_to_user_id: selectedUserId.value,
        assignment_reason: assignmentReason.value.trim() || 'Manager manual assignment'
      })
    })

    if (res.ok) {
      emit('assigned')
      close()
    } else {
      const err = await res.json()
      errorMessage.value = err.detail || 'Failed to assign lead.'
    }
  } catch (err) {
    errorMessage.value = err.message
  } finally {
    isSubmitting.value = false
  }
}

const close = () => {
  emit('close')
}
</script>

