<template>
  <aside 
    class="bg-[#171717] border-r border-[#2f2f2f] flex flex-col h-full transition-all duration-200 select-none z-20"
    :class="isOpen ? 'w-80 min-w-80' : 'w-0 min-w-0 overflow-hidden border-none'"
  >
    <!-- Top Action: New Chat & Close -->
    <div class="p-3.5 flex items-center justify-between border-b border-white/5">
      <button 
        @click="$emit('new-chat')" 
        class="flex-1 flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm font-medium text-gray-200 hover:text-white bg-[#212121] hover:bg-[#282828] border border-white/10 transition shadow-sm group"
      >
        <Plus class="w-4 h-4 text-emerald-400 group-hover:rotate-90 transition-transform duration-200" />
        <span>New Chat</span>
      </button>

      <button 
        @click="$emit('toggle-sidebar')" 
        class="p-2 ml-2 text-gray-400 hover:text-white rounded-lg hover:bg-white/5 transition"
        title="Close sidebar"
      >
        <PanelLeftClose class="w-4 h-4" />
      </button>
    </div>

    <!-- Scrollable Middle Section: History & Loan Profile Controls -->
    <div class="flex-1 overflow-y-auto px-3 py-3 space-y-4">
      <!-- Chat Sessions Section -->
      <div>
        <div class="px-2 pb-1.5 text-[11px] font-semibold uppercase tracking-wider text-gray-400 flex items-center justify-between">
          <span>Conversations</span>
          <span class="text-gray-400 text-[10px]">{{ sessions.length }}</span>
        </div>
        <div class="space-y-1">
          <div 
            v-for="s in sessions" 
            :key="s.id"
            @click="$emit('select-session', s.id)"
            class="group flex items-center justify-between px-3 py-2 rounded-lg text-xs cursor-pointer transition border"
            :class="activeSessionId === s.id ? 'bg-[#262626] text-white border-white/15' : 'text-gray-400 hover:text-gray-200 hover:bg-[#212121] border-transparent'"
          >
            <div class="flex items-center gap-2 truncate">
              <MessageSquare class="w-3.5 h-3.5 flex-shrink-0 text-gray-400 group-hover:text-emerald-400 transition" />
              <span class="truncate">{{ s.title || 'Loan Inquiry' }}</span>
            </div>
            <button 
              v-if="sessions.length > 1" 
              @click.stop="$emit('delete-session', s.id)"
              class="opacity-0 group-hover:opacity-100 p-1 hover:text-red-400 transition"
              title="Delete chat"
            >
              <Trash2 class="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>

      <!-- Applicant Profile & Filter Presets -->
      <div class="pt-2 border-t border-white/5">
        <button 
          @click="profileOpen = !profileOpen"
          class="w-full flex items-center justify-between px-2 py-1 text-[11px] font-semibold uppercase tracking-wider text-gray-400 hover:text-gray-200 transition"
        >
          <span class="flex items-center gap-1.5">
            <SlidersHorizontal class="w-3.5 h-3.5 text-emerald-400" />
            Borrower Profile & Filters
          </span>
          <ChevronDown class="w-3.5 h-3.5 transition-transform" :class="{ 'rotate-180': profileOpen }" />
        </button>

        <div v-show="profileOpen" class="mt-2.5 space-y-3 px-1 text-xs">
          <!-- Loan Category Filter -->
          <div>
            <label class="block text-gray-400 text-[11px] font-medium mb-1">Loan Category</label>
            <select 
              :value="profile.category" 
              @change="updateProfile('category', $event.target.value)"
              class="w-full bg-[#212121] border border-white/10 rounded-md px-2.5 py-1.5 text-xs text-gray-200 focus:outline-none focus:border-emerald-500 transition"
            >
              <option value="All">All Categories</option>
              <option value="Home Loan">Home Loan</option>
              <option value="Personal Loan">Personal Loan</option>
              <option value="Education Loan">Education Loan</option>
              <option value="Vehicle Loan">Vehicle Loan</option>
            </select>
          </div>

          <!-- Sector Filter -->
          <div>
            <label class="block text-gray-400 text-[11px] font-medium mb-1">Banking Sector</label>
            <select 
              :value="profile.sector" 
              @change="updateProfile('sector', $event.target.value)"
              class="w-full bg-[#212121] border border-white/10 rounded-md px-2.5 py-1.5 text-xs text-gray-200 focus:outline-none focus:border-emerald-500 transition"
            >
              <option value="All">All Sectors</option>
              <option value="Public">Public Sector Banks (SBI, BoB, etc.)</option>
              <option value="Private">Private Banks (HDFC, ICICI, etc.)</option>
              <option value="NBFC">NBFCs (Bajaj, Tata Capital, etc.)</option>
              <option value="Co-operative">Co-operative Banks</option>
            </select>
          </div>

          <!-- Employment Type -->
          <div>
            <label class="block text-gray-400 text-[11px] font-medium mb-1">Employment Type</label>
            <select 
              :value="profile.employment" 
              @change="updateProfile('employment', $event.target.value)"
              class="w-full bg-[#212121] border border-white/10 rounded-md px-2.5 py-1.5 text-xs text-gray-200 focus:outline-none focus:border-emerald-500 transition"
            >
              <option value="Salaried">Salaried</option>
              <option value="Self-Employed / Business">Self-Employed / Business</option>
              <option value="Student">Student</option>
              <option value="Pensioner">Pensioner</option>
              <option value="Doctor / Professional">Doctor / Professional</option>
              <option value="Other">Other</option>
            </select>
          </div>

          <!-- CIBIL Slider -->
          <div>
            <div class="flex justify-between items-center text-[11px] mb-1">
              <span class="text-gray-400 font-medium">CIBIL / Credit Score</span>
              <span class="font-bold font-mono" :class="scoreColor">{{ profile.cibil_score }}</span>
            </div>
            <input 
              type="range" 
              min="300" 
              max="900" 
              step="5"
              :value="profile.cibil_score" 
              @input="updateProfile('cibil_score', Number($event.target.value))"
              class="w-full accent-emerald-500 bg-[#282828] h-1.5 rounded-lg appearance-none cursor-pointer"
            />
            <div class="flex justify-between text-[10px] text-gray-400 mt-0.5">
              <span>300</span>
              <span>750 (Prime)</span>
              <span>900</span>
            </div>
          </div>

          <!-- Monthly Income -->
          <div>
            <label class="block text-gray-400 text-[11px] font-medium mb-1">Monthly Income</label>
            <input 
              type="text" 
              :value="profile.income" 
              @input="updateProfile('income', $event.target.value)"
              placeholder="e.g. Rs. 75,000 / month" 
              class="w-full bg-[#212121] border border-white/10 rounded-md px-2.5 py-1.5 text-xs text-gray-200 placeholder-gray-600 focus:outline-none focus:border-emerald-500 transition"
            />
          </div>

          <!-- Requested Amount -->
          <div>
            <label class="block text-gray-400 text-[11px] font-medium mb-1">Target Loan Amount</label>
            <input 
              type="text" 
              :value="profile.requested_amount" 
              @input="updateProfile('requested_amount', $event.target.value)"
              placeholder="e.g. Rs. 25 Lakhs" 
              class="w-full bg-[#212121] border border-white/10 rounded-md px-2.5 py-1.5 text-xs text-gray-200 placeholder-gray-600 focus:outline-none focus:border-emerald-500 transition"
            />
          </div>

          <button 
            @click="$emit('reset-profile')" 
            class="w-full py-1.5 text-[11px] text-gray-400 hover:text-white hover:bg-white/5 rounded border border-white/5 transition"
          >
            Reset Filters to Default
          </button>
        </div>
      </div>
    </div>

    <!-- Bottom Footer Metrics -->
    <div class="p-3 border-t border-white/5 bg-[#141414] text-[11px] text-gray-400">
      <div class="flex items-center justify-between mb-1.5">
        <span class="flex items-center gap-1.5 text-gray-300 font-medium">
          <Shield class="w-3.5 h-3.5 text-emerald-400" />
          FinNav Grounded RAG
        </span>
        <span class="text-[10px] bg-emerald-500/10 text-emerald-400 px-1.5 py-0.5 rounded border border-emerald-500/20">
          Live
        </span>
      </div>
      <div class="flex justify-between text-[10px] text-gray-400">
        <span>163 Schemes</span>
        <span>•</span>
        <span>34 Institutions</span>
        <span>•</span>
        <span>LangGraph</span>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { ref, computed } from 'vue'
import { 
  Plus, 
  PanelLeftClose, 
  MessageSquare, 
  Trash2, 
  SlidersHorizontal, 
  ChevronDown, 
  Shield 
} from 'lucide-vue-next'

const props = defineProps({
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
  },
  profile: {
    type: Object,
    required: true
  }
})

const emit = defineEmits([
  'toggle-sidebar', 
  'new-chat', 
  'select-session', 
  'delete-session', 
  'update-profile', 
  'reset-profile'
])

const profileOpen = ref(true)

const updateProfile = (key, value) => {
  emit('update-profile', { ...props.profile, [key]: value })
}

const scoreColor = computed(() => {
  const s = props.profile.cibil_score
  if (s >= 750) return 'text-emerald-400'
  if (s >= 650) return 'text-amber-400'
  return 'text-rose-400'
})
</script>

