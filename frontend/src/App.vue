<template>
  <div class="flex h-screen w-screen overflow-hidden bg-[#212121] text-[#ececec]">
    <!-- Collapsible Sidebar -->
    <Sidebar 
      :is-open="sidebarOpen"
      :sessions="sessions"
      :active-session-id="activeSessionId"
      :profile="activeSession.profile"
      @toggle-sidebar="sidebarOpen = !sidebarOpen"
      @new-chat="createNewSession"
      @select-session="switchSession"
      @delete-session="deleteSession"
      @update-profile="updateCurrentProfile"
      @reset-profile="resetCurrentProfile"
    />

    <!-- Main Chat Workspace -->
    <main class="flex-1 flex flex-col h-full min-w-0 relative">
      <!-- Top Navigation Bar -->
      <header class="h-14 border-b border-[#2f2f2f] flex items-center justify-between px-4 bg-[#212121]/90 backdrop-blur z-10">
        <div class="flex items-center gap-3">
          <!-- Toggle Sidebar Button -->
          <button 
            @click="sidebarOpen = !sidebarOpen"
            class="p-2 text-gray-400 hover:text-white rounded-lg hover:bg-white/5 transition"
            :title="sidebarOpen ? 'Hide sidebar' : 'Show sidebar'"
          >
            <PanelLeftOpen v-if="!sidebarOpen" class="w-5 h-5" />
            <PanelLeftClose v-else class="w-5 h-5 md:hidden" />
          </button>

          <!-- Model & System Info Pill -->
          <div class="flex items-center gap-2">
            <div class="flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#2a2a2a] border border-white/10 text-xs font-medium text-gray-200">
              <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              <span>FinNav Advisor</span>
              <span class="text-gray-400">·</span>
              <span class="text-emerald-400 font-mono text-[11px]">{{ apiStatus.model || 'Qwen 3.8' }}</span>
            </div>
            
            <div class="hidden sm:flex items-center gap-1 text-[11px] text-gray-400">
              <span class="px-2 py-0.5 rounded bg-white/5 border border-white/10">163 Verified Schemes</span>
            </div>
          </div>
        </div>

        <!-- Top Right Actions -->
        <div class="flex items-center gap-2">
          <button 
            v-if="activeSession.messages.length > 0"
            @click="clearCurrentChat" 
            class="text-xs text-gray-400 hover:text-white px-2.5 py-1.5 rounded-md hover:bg-white/5 transition flex items-center gap-1.5"
            title="Clear current screen messages"
          >
            <Eraser class="w-3.5 h-3.5" />
            <span class="hidden sm:inline">Clear Chat</span>
          </button>

          <button 
            @click="createNewSession" 
            class="text-xs bg-emerald-600 hover:bg-emerald-500 text-white font-medium px-3 py-1.5 rounded-lg transition shadow-sm flex items-center gap-1.5"
          >
            <Plus class="w-3.5 h-3.5" />
            <span class="hidden sm:inline">New Session</span>
          </button>
        </div>
      </header>

      <!-- Scrollable Conversation Canvas -->
      <div 
        ref="chatContainer"
        class="flex-1 overflow-y-auto overflow-x-hidden scroll-smooth relative"
      >
        <!-- Empty State Hero with Quick Prompts -->
        <div v-if="activeSession.messages.length === 0" class="h-full flex items-center justify-center">
          <QuickPrompts 
            :prompts="quickPrompts" 
            @select-prompt="handlePromptSelect" 
          />
        </div>

        <!-- Message Stream -->
        <div v-else class="pb-36 pt-4">
          <ChatMessage 
            v-for="(msg, idx) in activeSession.messages" 
            :key="idx" 
            :message="msg" 
          />
        </div>

        <div ref="bottomAnchor"></div>
      </div>

      <!-- Bottom Docked Floating Input Bar -->
      <div class="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-[#212121] via-[#212121]/95 to-transparent pointer-events-none">
        <div class="max-w-3xl mx-auto pointer-events-auto">
          <!-- Textarea Input Box -->
          <div class="relative bg-[#2f2f2f] rounded-2xl border border-white/10 shadow-2xl focus-within:border-white/20 transition-all p-2 flex items-end gap-2">
            <textarea
              ref="textareaRef"
              v-model="inputQuery"
              @keydown="handleKeydown"
              @input="adjustTextareaHeight"
              rows="1"
              placeholder="Ask about interest rates, compare schemes, or calculate EMIs..."
              class="flex-1 bg-transparent border-0 text-white placeholder-gray-400 text-sm px-3 py-2.5 resize-none focus:outline-none max-h-48 leading-relaxed"
            ></textarea>

            <button
              @click="submitQuery"
              :disabled="!canSubmit"
              class="w-9 h-9 rounded-xl flex items-center justify-center transition flex-shrink-0 mb-0.5 shadow-sm"
              :class="canSubmit ? 'bg-white text-black hover:bg-gray-200 cursor-pointer' : 'bg-white/10 text-gray-500 cursor-not-allowed'"
              title="Send message"
            >
              <ArrowUp class="w-5 h-5 font-bold" />
            </button>
          </div>

          <!-- Legal / Precision Disclaimer -->
          <p class="text-center text-[11px] text-gray-400 mt-2 px-2">
            FinNav answers are strictly grounded on official bank filings from RBI, SBI, HDFC, and NBFC portals. Verify all terms with your lender.
          </p>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { 
  PanelLeftOpen, 
  PanelLeftClose, 
  Plus, 
  Eraser, 
  ArrowUp 
} from 'lucide-vue-next'
import Sidebar from './components/Sidebar.vue'
import ChatMessage from './components/ChatMessage.vue'
import QuickPrompts from './components/QuickPrompts.vue'

const sidebarOpen = ref(true)
const inputQuery = ref('')
const isLoading = ref(false)
const chatContainer = ref(null)
const bottomAnchor = ref(null)
const textareaRef = ref(null)

const apiStatus = reactive({
  status: 'connecting',
  model: 'qwen/qwen3.8-27b',
  schemes: 163
})

const defaultProfile = () => ({
  employment: 'Salaried',
  cibil_score: 750,
  income: '',
  requested_amount: '',
  category: 'All',
  sector: 'All'
})

const quickPrompts = ref([
  {
    title: "Compare Education Loans",
    prompt: "Compare SBI Scholar Loan vs Canara Vidya Turant",
    badge: "Comparison"
  },
  {
    title: "EBLR vs MCLR Benchmark",
    prompt: "What is EBLR vs MCLR and which is better?",
    badge: "Regulation"
  },
  {
    title: "Calculate Loan EMI",
    prompt: "Calculate EMI for 20 Lakhs at 8.75% for 7 years",
    badge: "Calculator"
  },
  {
    title: "Doctor Overdraft Loan",
    prompt: "Doctor wanting flexible overdraft personal loan",
    badge: "Advisory"
  }
])

// Sessions state
const sessions = ref([])
const activeSessionId = ref('')

// Initialize or load sessions from localStorage
const loadStoredSessions = () => {
  try {
    const raw = localStorage.getItem('finnav_sessions')
    if (raw) {
      const parsed = JSON.parse(raw)
      if (Array.isArray(parsed) && parsed.length > 0) {
        sessions.value = parsed
        activeSessionId.value = parsed[0].id
        return
      }
    }
  } catch (e) {
    console.error('Failed to load sessions from localStorage:', e)
  }

  // Create initial fresh session
  createNewSession()
}

const saveSessions = () => {
  try {
    localStorage.setItem('finnav_sessions', JSON.stringify(sessions.value))
  } catch (e) {
    console.error('Failed to save sessions:', e)
  }
}

const createNewSession = () => {
  const newId = `chat_${Math.random().toString(36).substring(2, 10)}`
  const newSession = {
    id: newId,
    title: 'New Loan Inquiry',
    createdAt: Date.now(),
    profile: defaultProfile(),
    messages: []
  }
  sessions.value.unshift(newSession)
  activeSessionId.value = newId
  saveSessions()
  nextTick(() => {
    if (textareaRef.value) textareaRef.value.focus()
  })
}

const activeSession = computed(() => {
  const found = sessions.value.find(s => s.id === activeSessionId.value)
  return found || {
    id: activeSessionId.value,
    title: 'New Session',
    profile: defaultProfile(),
    messages: []
  }
})

const switchSession = (id) => {
  activeSessionId.value = id
  scrollToBottom()
}

const deleteSession = (id) => {
  sessions.value = sessions.value.filter(s => s.id !== id)
  if (sessions.value.length === 0) {
    createNewSession()
  } else if (activeSessionId.value === id) {
    activeSessionId.value = sessions.value[0].id
  }
  saveSessions()
}

const clearCurrentChat = () => {
  const cur = sessions.value.find(s => s.id === activeSessionId.value)
  if (cur) {
    cur.messages = []
    saveSessions()
  }
}

const updateCurrentProfile = (newProfile) => {
  const cur = sessions.value.find(s => s.id === activeSessionId.value)
  if (cur) {
    cur.profile = newProfile
    saveSessions()
  }
}

const resetCurrentProfile = () => {
  updateCurrentProfile(defaultProfile())
}

const canSubmit = computed(() => {
  return inputQuery.value.trim().length > 0 && !isLoading.value
})

const adjustTextareaHeight = () => {
  if (!textareaRef.value) return
  textareaRef.value.style.height = 'auto'
  textareaRef.value.style.height = `${Math.min(textareaRef.value.scrollHeight, 200)}px`
}

const scrollToBottom = () => {
  nextTick(() => {
    if (bottomAnchor.value) {
      bottomAnchor.value.scrollIntoView({ behavior: 'smooth' })
    }
  })
}

const handleKeydown = (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    if (canSubmit.value) {
      submitQuery()
    }
  }
}

const handlePromptSelect = (promptText) => {
  inputQuery.value = promptText
  submitQuery()
}

const submitQuery = async () => {
  const query = inputQuery.value.trim()
  if (!query || isLoading.value) return

  const cur = sessions.value.find(s => s.id === activeSessionId.value)
  if (!cur) return

  // Update session title if first message
  if (cur.messages.length === 0) {
    cur.title = query.length > 28 ? query.substring(0, 28) + '...' : query
  }

  // Append user message
  cur.messages.push({
    role: 'user',
    content: query
  })

  // Append loading assistant message
  const assistantMsgIndex = cur.messages.length
  cur.messages.push({
    role: 'assistant',
    content: '',
    intent: '',
    candidates: [],
    loading: true
  })

  inputQuery.value = ''
  if (textareaRef.value) {
    textareaRef.value.style.height = 'auto'
  }
  isLoading.value = true
  scrollToBottom()

  try {
    const payload = {
      chat_id: cur.id,
      query: query,
      user_profile: cur.profile
    }

    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    })

    if (!response.ok) {
      throw new Error(`API error: ${response.status} ${response.statusText}`)
    }

    const data = await response.json()

    // Update assistant message with response
    cur.messages[assistantMsgIndex] = {
      role: 'assistant',
      content: data.final_response,
      intent: data.intent,
      candidates: data.candidates || [],
      loading: false
    }
  } catch (error) {
    console.error('Chat request failed:', error)
    cur.messages[assistantMsgIndex] = {
      role: 'assistant',
      content: `⚠️ **Connection Error**: Unable to reach FinNav API. Please verify the backend server is running.\n\n*Error details: ${error.message}*`,
      intent: 'ERROR',
      candidates: [],
      loading: false
    }
  } finally {
    isLoading.value = false
    saveSessions()
    scrollToBottom()
  }
}

onMounted(async () => {
  loadStoredSessions()

  // Fetch health check
  try {
    const res = await fetch('/api/health')
    if (res.ok) {
      const data = await res.json()
      apiStatus.status = 'connected'
      apiStatus.model = data.model || 'qwen/qwen3.8-27b'
      apiStatus.schemes = data.verified_schemes || 163
    }
  } catch (e) {
    console.warn('Backend API not yet reachable at /api/health')
  }

  // Fetch presets if available
  try {
    const res = await fetch('/api/presets')
    if (res.ok) {
      const data = await res.json()
      if (data.quick_prompts && data.quick_prompts.length > 0) {
        quickPrompts.value = data.quick_prompts
      }
    }
  } catch (e) {
    // Keep defaults
  }
})
</script>

