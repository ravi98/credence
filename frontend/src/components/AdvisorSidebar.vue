<template>
  <aside 
    class="bg-white border-r border-surface-border flex flex-col h-full transition-all duration-200 select-none z-20"
    :class="isOpen ? 'w-72 min-w-72' : 'w-0 min-w-0 overflow-hidden border-none'"
  >
    <!-- Top Action: Brand, New Chat & Close -->
    <div class="p-3.5 border-b border-surface-border space-y-3">
      <div class="flex items-center justify-between">
        <router-link to="/" class="flex items-center gap-2 text-brand-deep font-bold text-sm">
          <div class="w-6 h-6 rounded bg-brand flex items-center justify-center text-white text-xs">
            <Landmark class="w-3.5 h-3.5" />
          </div>
          <span>Cred<span class="text-brand">ence</span></span>
        </router-link>
        <button 
          @click="$emit('toggle-sidebar')" 
          class="p-1.5 text-brand-muted hover:text-brand-deep rounded hover:bg-surface-secondary transition"
          title="Close navigation"
        >
          <PanelLeftClose class="w-4 h-4" />
        </button>
      </div>

      <button 
        @click="$emit('new-chat')" 
        class="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-xs font-semibold text-white bg-brand hover:bg-brand-hover shadow-sm transition"
      >
        <Plus class="w-4 h-4" />
        <span>New Conversation</span>
      </button>
    </div>

    <!-- Recent Conversations List -->
    <div class="flex-1 overflow-y-auto px-3 py-3 space-y-3">
      <div>
        <div class="px-2 pb-1.5 text-[10px] font-bold uppercase tracking-wider text-brand-muted flex items-center justify-between">
          <span>Recent Inquiries</span>
          <span class="text-[10px] bg-surface-secondary px-1.5 py-0.2 rounded">{{ sessions.length }}</span>
        </div>
        <div class="space-y-1">
          <div 
            v-for="s in sessions" 
            :key="s.id"
            @click="$emit('select-session', s.id)"
            class="group flex items-center justify-between px-3 py-2 rounded-lg text-xs cursor-pointer transition border"
            :class="activeSessionId === s.id ? 'bg-surface-light text-brand font-semibold border-brand/20' : 'text-brand-deep hover:bg-surface-secondary border-transparent'"
          >
            <div class="flex items-center gap-2 truncate">
              <MessageSquare class="w-3.5 h-3.5 flex-shrink-0 text-brand-icon" />
              <span class="truncate">{{ s.title || 'Loan Inquiry' }}</span>
            </div>
            <button 
              v-if="sessions.length > 1" 
              @click.stop="$emit('delete-session', s.id)"
              class="opacity-0 group-hover:opacity-100 p-1 hover:text-red-600 transition"
              title="Delete conversation"
            >
              <Trash2 class="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>

      <!-- Quick Platform Navigation -->
      <div class="pt-3 border-t border-surface-border space-y-1">
        <div class="px-2 pb-1 text-[10px] font-bold uppercase tracking-wider text-brand-muted">
          Platform Tools
        </div>
        <router-link 
          to="/explore" 
          class="flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs text-brand-deep hover:bg-surface-secondary transition"
        >
          <Layers class="w-3.5 h-3.5 text-brand-icon" />
          <span>Explore 163 Schemes</span>
        </router-link>
        <router-link 
          to="/compare" 
          class="flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs text-brand-deep hover:bg-surface-secondary transition"
        >
          <Scale class="w-3.5 h-3.5 text-brand-icon" />
          <span>Side-by-Side Comparison</span>
        </router-link>
        <router-link 
          to="/calculators/emi" 
          class="flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs text-brand-deep hover:bg-surface-secondary transition"
        >
          <Calculator class="w-3.5 h-3.5 text-brand-icon" />
          <span>EMI Calculator</span>
        </router-link>
        <router-link 
          to="/learn" 
          class="flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs text-brand-deep hover:bg-surface-secondary transition"
        >
          <BookOpen class="w-3.5 h-3.5 text-brand-icon" />
          <span>Credence Learn Hub</span>
        </router-link>
      </div>
    </div>

    <!-- Bottom Footer Metrics -->
    <div class="p-3 border-t border-surface-border bg-surface-canvas text-xs text-brand-muted">
      <div class="flex items-center justify-between mb-1">
        <span class="flex items-center gap-1.5 text-brand-deep font-semibold text-[11px]">
          <ShieldCheck class="w-3.5 h-3.5 text-sage" />
          Closed-Domain RAG
        </span>
        <span class="text-[10px] bg-sage-light text-sage font-semibold px-1.5 py-0.5 rounded border border-sage-border">
          Active
        </span>
      </div>
      <div class="text-[10px] text-brand-muted">
        163 Schemes · 34 Banks · Groq Qwen
      </div>
    </div>
  </aside>
</template>

<script setup>
import { 
  Landmark, 
  Plus, 
  PanelLeftClose, 
  MessageSquare, 
  Trash2, 
  Layers, 
  Scale, 
  Calculator, 
  BookOpen, 
  ShieldCheck 
} from 'lucide-vue-next'

defineProps({
  isOpen: {
    type: Boolean,
    default: true
  },
  sessions: {
    type: Array,
    default: () => []
  },
  activeSessionId: {
    type: String,
    required: true
  }
})

defineEmits([
  'toggle-sidebar', 
  'new-chat', 
  'select-session', 
  'delete-session'
])
</script>

