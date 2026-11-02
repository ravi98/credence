<template>
  <div class="space-y-4">
    <!-- Post Note Box -->
    <div class="p-4 rounded-2xl bg-white border border-surface-border space-y-3">
      <h4 class="text-xs font-bold uppercase tracking-wider text-brand-deep">
        Add Internal Collaboration Note
      </h4>
      <textarea 
        v-model="newNoteText"
        rows="2"
        placeholder="Record call summary, borrower requirements, lender feedback, or next action..."
        class="w-full text-xs sm:text-sm p-3 rounded-xl border border-surface-border focus:border-brand focus:ring-1 focus:ring-brand outline-none"
      ></textarea>
      <div class="flex items-center justify-between">
        <span class="text-[11px] text-brand-muted">Visible to internal sales & underwriting team only.</span>
        <button 
          @click="submitNote"
          :disabled="isSubmitting || !newNoteText.trim()"
          class="px-4 py-2 rounded-xl bg-brand text-white text-xs font-bold shadow-xs hover:bg-brand-hover disabled:opacity-50 transition cursor-pointer"
        >
          <span>{{ isSubmitting ? 'Posting...' : 'Post Note' }}</span>
        </button>
      </div>
    </div>

    <!-- Notes List -->
    <div v-if="notes.length === 0" class="p-6 rounded-2xl bg-white border border-surface-border text-center text-xs text-brand-muted">
      No internal notes logged yet for this lead.
    </div>

    <div v-else class="space-y-2.5">
      <div 
        v-for="note in notes" 
        :key="note.id"
        class="p-4 rounded-2xl bg-white border border-surface-border space-y-1.5"
      >
        <div class="flex items-center justify-between gap-2 text-xs">
          <strong class="font-bold text-brand-deep">{{ note.author_name }}</strong>
          <span class="text-brand-muted text-[11px] font-mono">{{ formatDate(note.created_at) }}</span>
        </div>
        <p class="text-xs sm:text-sm text-brand-deep leading-relaxed whitespace-pre-wrap">
          {{ note.note_content }}
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  leadId: {
    type: String,
    required: true
  },
  notes: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['note-added'])

const newNoteText = ref('')
const isSubmitting = ref(false)

const submitNote = async () => {
  if (!newNoteText.value.trim() || isSubmitting.value) return
  isSubmitting.value = true

  try {
    const token = localStorage.getItem('credence_sales_token')
    const res = await fetch(`/api/sales/leads/${props.leadId}/notes`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ note_content: newNoteText.value.trim() })
    })

    if (res.ok) {
      newNoteText.value = ''
      emit('note-added')
    }
  } catch (err) {
    console.error('Failed to post note:', err)
  } finally {
    isSubmitting.value = false
  }
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

