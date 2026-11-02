<template>
  <div class="space-y-4">
    <!-- Schedule Task Box -->
    <div class="p-4 rounded-2xl bg-white border border-surface-border space-y-3">
      <div class="flex items-center justify-between">
        <h4 class="text-xs font-bold uppercase tracking-wider text-brand-deep">
          Schedule Follow-up Task
        </h4>
        <button 
          @click="showCreateForm = !showCreateForm"
          class="text-xs font-bold text-brand hover:text-brand-hover cursor-pointer"
        >
          {{ showCreateForm ? 'Close Form' : '+ New Task' }}
        </button>
      </div>

      <div v-if="showCreateForm" class="space-y-3 pt-2 border-t border-surface-border">
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label class="block text-[11px] font-bold text-brand-muted mb-1">Task Type</label>
            <select 
              v-model="newTask.taskType"
              class="w-full text-xs px-3 py-2 rounded-xl border border-surface-border bg-white"
            >
              <option value="Callback">Borrower Phone Callback</option>
              <option value="Document Collection">Document Collection</option>
              <option value="Bank Sanction Follow-up">Bank Sanction Follow-up</option>
              <option value="Lender Rate Negotiation">Lender Rate Negotiation</option>
              <option value="Verification Visit">Verification Visit</option>
            </select>
          </div>

          <div>
            <label class="block text-[11px] font-bold text-brand-muted mb-1">Due Date & Time</label>
            <input 
              v-model="newTask.dueAt"
              type="datetime-local"
              class="w-full text-xs px-3 py-2 rounded-xl border border-surface-border bg-white"
            />
          </div>
        </div>

        <div>
          <label class="block text-[11px] font-bold text-brand-muted mb-1">Task Details</label>
          <input 
            v-model="newTask.description"
            type="text"
            placeholder="e.g. Call to verify Form 16 / ITR computation status."
            class="w-full text-xs px-3 py-2 rounded-xl border border-surface-border focus:border-brand outline-none"
          />
        </div>

        <div class="flex justify-end">
          <button 
            @click="submitTask"
            :disabled="isSubmitting || !newTask.description.trim() || !newTask.dueAt"
            class="px-4 py-2 rounded-xl bg-brand text-white text-xs font-bold shadow-xs hover:bg-brand-hover disabled:opacity-50 transition cursor-pointer"
          >
            <span>{{ isSubmitting ? 'Scheduling...' : 'Save Task' }}</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Tasks List -->
    <div v-if="tasks.length === 0" class="p-6 rounded-2xl bg-white border border-surface-border text-center text-xs text-brand-muted">
      No pending tasks for this lead.
    </div>

    <div v-else class="space-y-2.5">
      <div 
        v-for="task in tasks" 
        :key="task.id"
        class="p-4 rounded-2xl bg-white border border-surface-border flex items-center justify-between gap-3 transition"
        :class="task.status === 'COMPLETED' ? 'opacity-60 bg-surface-canvas' : 'hover:border-brand/30'"
      >
        <div class="flex items-start gap-3 min-w-0">
          <button 
            @click="toggleComplete(task)"
            :disabled="task.status === 'COMPLETED'"
            class="mt-0.5 w-5 h-5 rounded-md border flex items-center justify-center transition cursor-pointer"
            :class="task.status === 'COMPLETED' ? 'bg-sage border-sage text-white' : 'border-surface-border hover:border-brand text-transparent'"
          >
            <Check class="w-3.5 h-3.5" />
          </button>

          <div class="min-w-0">
            <div class="flex items-center gap-2 flex-wrap">
              <span class="text-[10px] font-extrabold uppercase px-2 py-0.5 rounded-md bg-surface-secondary text-brand-deep">
                {{ task.task_type }}
              </span>
              <span class="text-xs font-semibold text-brand-deep truncate">
                {{ task.description }}
              </span>
            </div>
            <div class="flex items-center gap-2 text-[11px] text-brand-muted mt-1">
              <span>Assigned to {{ task.assigned_to_name }}</span>
              <span>·</span>
              <span :class="isOverdue(task.due_at, task.status) ? 'text-red-600 font-bold' : ''">
                Due: {{ formatDate(task.due_at) }}
              </span>
            </div>
          </div>
        </div>

        <span 
          class="text-[11px] font-bold px-2 py-0.5 rounded-md self-center flex-shrink-0"
          :class="task.status === 'COMPLETED' ? 'bg-sage/10 text-sage' : (isOverdue(task.due_at, task.status) ? 'bg-red-50 text-red-700' : 'bg-blue-50 text-blue-700')"
        >
          {{ task.status }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { Check } from 'lucide-vue-next'

const props = defineProps({
  leadId: {
    type: String,
    required: true
  },
  tasks: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['task-updated'])

const showCreateForm = ref(false)
const isSubmitting = ref(false)

const newTask = reactive({
  taskType: 'Callback',
  description: '',
  dueAt: ''
})

const submitTask = async () => {
  if (!newTask.description.trim() || !newTask.dueAt || isSubmitting.value) return
  isSubmitting.value = true

  try {
    const token = localStorage.getItem('credence_sales_token')
    const dueIso = new Date(newTask.dueAt).toISOString()

    const res = await fetch(`/api/sales/leads/${props.leadId}/tasks`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        task_type: newTask.taskType,
        description: newTask.description.trim(),
        due_at: dueIso
      })
    })

    if (res.ok) {
      newTask.description = ''
      newTask.dueAt = ''
      showCreateForm.value = false
      emit('task-updated')
    }
  } catch (err) {
    console.error('Failed to create task:', err)
  } finally {
    isSubmitting.value = false
  }
}

const toggleComplete = async (task) => {
  if (task.status === 'COMPLETED') return

  try {
    const token = localStorage.getItem('credence_sales_token')
    const res = await fetch(`/api/sales/tasks/${task.id}/complete`, {
      method: 'PATCH',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    if (res.ok) {
      emit('task-updated')
    }
  } catch (err) {
    console.error('Failed to complete task:', err)
  }
}

const isOverdue = (dueStr, status) => {
  if (status === 'COMPLETED' || !dueStr) return false
  return new Date(dueStr) < new Date()
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  try {
    const d = new Date(dateStr)
    return d.toLocaleString('en-IN', { 
      day: 'numeric', 
      month: 'short', 
      hour: '2-digit', 
      minute: '2-digit' 
    })
  } catch (e) {
    return dateStr
  }
}
</script>

