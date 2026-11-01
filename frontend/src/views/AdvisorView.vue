<template>
  <div class="flex h-screen w-screen overflow-hidden bg-surface-canvas text-brand-deep relative">
    <!-- Left Navigation Sidebar -->
    <AdvisorSidebar 
      :is-open="sidebarOpen"
      :sessions="sessions"
      :active-session-id="activeSessionId"
      @toggle-sidebar="sidebarOpen = !sidebarOpen"
      @new-chat="createNewSession"
      @select-session="switchSession"
      @delete-session="deleteSession"
    />

    <!-- Main Central Conversation Workspace -->
    <main class="flex-1 flex flex-col h-full min-w-0 relative">
      <!-- Top Application Header -->
      <header class="h-16 border-b border-surface-border flex items-center justify-between px-4 sm:px-6 bg-white/95 backdrop-blur z-10 flex-shrink-0">
        <div class="flex items-center gap-2.5 sm:gap-3 min-w-0">
          <!-- Toggle Sidebar -->
          <button 
            @click="sidebarOpen = !sidebarOpen"
            class="p-2 text-brand-muted hover:text-brand-deep rounded-lg hover:bg-surface-secondary transition flex-shrink-0"
            :title="sidebarOpen ? 'Hide navigation' : 'Show navigation'"
          >
            <PanelLeftOpen v-if="!sidebarOpen" class="w-5 h-5" />
            <PanelLeftClose v-else class="w-5 h-5" />
          </button>

          <!-- Model & System Info Pill -->
          <div class="flex items-center gap-2 min-w-0">
            <div class="flex items-center gap-2 px-3 py-1.5 rounded-full bg-surface-secondary border border-surface-border text-xs sm:text-sm font-semibold text-brand truncate">
              <span class="w-2.5 h-2.5 rounded-full bg-sage animate-pulse flex-shrink-0"></span>
              <span class="truncate">Credence Advisor</span>
              <span class="text-brand-muted hidden xs:inline">·</span>
              <span class="font-mono text-xs hidden xs:inline">{{ apiStatus.model || 'Qwen 3.8' }}</span>
            </div>
            
            <div class="hidden lg:flex items-center gap-1 text-xs text-brand-muted font-medium flex-shrink-0">
              <span class="px-2.5 py-1 rounded-md bg-white border border-surface-border">163 Verified Schemes</span>
            </div>
          </div>
        </div>

        <!-- Top Right Actions -->
        <div class="flex items-center gap-2 sm:gap-2.5 flex-shrink-0">
          <!-- Clear current screen -->
          <button 
            v-if="activeSession.messages.length > 0"
            @click="clearCurrentChat" 
            class="text-xs sm:text-sm text-brand-muted hover:text-brand-deep px-2.5 sm:px-3 py-1.5 rounded-md hover:bg-surface-secondary transition flex items-center gap-1.5 font-medium"
            title="Clear current messages"
          >
            <Eraser class="w-4 h-4" />
            <span class="hidden sm:inline">Clear</span>
          </button>

          <!-- Borrower Profile Drawer Toggle Button -->
          <button 
            @click="profileDrawerOpen = !profileDrawerOpen"
            class="text-xs sm:text-sm font-semibold px-3 py-1.5 sm:px-3.5 sm:py-2 rounded-lg border transition shadow-2xs flex items-center gap-2"
            :class="hasCustomFilters ? 'bg-surface-light border-brand/30 text-brand' : 'bg-white border-surface-border text-brand-deep hover:bg-surface-secondary'"
          >
            <SlidersHorizontal class="w-4 h-4 text-brand" />
            <span class="hidden xs:inline">Profile & Filters</span>
            <span class="xs:hidden">Filters</span>
            <span v-if="hasCustomFilters" class="w-2 h-2 rounded-full bg-brand"></span>
          </button>
        </div>
      </header>

      <!-- Scrollable Conversation Canvas -->
      <div 
        ref="chatContainer"
        class="flex-1 overflow-y-auto overflow-x-hidden scroll-smooth relative"
      >
        <!-- First-Time Welcome Screen -->
        <div v-if="activeSession.messages.length === 0" class="min-h-full py-10 px-4 flex flex-col items-center justify-center">
          <AdvisorWelcome 
            @select-prompt="handlePromptSelect"
            @select-category="handleCategorySelect"
          />
        </div>

        <!-- Message Stream -->
        <div v-else class="pb-48 sm:pb-56 pt-4">
          <ChatMessage 
            v-for="(msg, idx) in activeSession.messages" 
            :key="idx" 
            :message="msg"
            @select-suggestion="handlePromptSelect"
          />
        </div>

        <div ref="bottomAnchor"></div>
      </div>

      <!-- Bottom Docked Floating Input Bar -->
      <div class="absolute bottom-0 left-0 right-0 p-3 sm:p-5 bg-gradient-to-t from-surface-canvas via-surface-canvas/95 to-transparent pointer-events-none">
        <div class="max-w-3xl mx-auto pointer-events-auto">
          <!-- Textarea Input Box -->
          <div class="relative bg-white rounded-2xl border border-surface-border shadow-md focus-within:border-brand/40 transition-all p-2.5 flex items-end gap-2.5">
            <textarea
              ref="textareaRef"
              v-model="inputQuery"
              @keydown="handleKeydown"
              @input="adjustTextareaHeight"
              rows="1"
              placeholder="Ask about interest rates, compare bank schemes, or calculate EMIs..."
              class="flex-1 bg-transparent border-0 text-brand-deep placeholder-brand-muted/70 text-sm sm:text-base px-3 py-2 sm:px-3.5 sm:py-2.5 resize-none focus:outline-none max-h-48 leading-relaxed font-sans"
            ></textarea>

            <button
              @click="submitQuery"
              :disabled="!canSubmit"
              class="w-10 h-10 rounded-xl flex items-center justify-center transition flex-shrink-0 mb-0.5 shadow-sm"
              :class="canSubmit ? 'bg-brand text-white hover:bg-brand-hover cursor-pointer' : 'bg-surface-secondary text-brand-muted/40 cursor-not-allowed'"
              title="Send message"
            >
              <ArrowUp class="w-5 h-5 font-bold" />
            </button>
          </div>

          <!-- Legal / Precision Disclaimer -->
          <p class="text-center text-xs text-brand-muted mt-2 px-2 truncate sm:whitespace-normal">
            Strictly grounded on official filings from RBI, SBI, HDFC, and 34 lenders. Deterministic calculations.
          </p>
        </div>
      </div>
    </main>

    <!-- Collapsible Borrower Profile Drawer (Right) -->
    <ProfileDrawer 
      :is-open="profileDrawerOpen"
      :profile="activeSession.profile"
      @close="profileDrawerOpen = false"
      @update-profile="updateCurrentProfile"
      @reset="resetCurrentProfile"
    />
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { 
  PanelLeftOpen, 
  PanelLeftClose, 
  Eraser, 
  SlidersHorizontal, 
  ArrowUp 
} from 'lucide-vue-next'
import AdvisorSidebar from '../components/AdvisorSidebar.vue'
import ProfileDrawer from '../components/ProfileDrawer.vue'
import ChatMessage from '../components/ChatMessage.vue'
import AdvisorWelcome from '../components/AdvisorWelcome.vue'

const route = useRoute()

const sidebarOpen = ref(true)
const profileDrawerOpen = ref(false)
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

// Sessions state
const sessions = ref([])
const activeSessionId = ref('')

const loadStoredSessions = () => {
  try {
    const raw = localStorage.getItem('credence_sessions') || localStorage.getItem('finnav_sessions')
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

  createNewSession()
}

const saveSessions = () => {
  try {
    localStorage.setItem('credence_sessions', JSON.stringify(sessions.value))
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

const hasCustomFilters = computed(() => {
  const p = activeSession.value.profile
  return (p.category && p.category !== 'All') || 
         (p.sector && p.sector !== 'All') || 
         p.cibil_score !== 750 || 
         !!p.income || 
         !!p.requested_amount
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

const handleCategorySelect = (categoryName) => {
  updateCurrentProfile({
    ...activeSession.value.profile,
    category: categoryName
  })
  inputQuery.value = `Recommend top ${categoryName} schemes`
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
      content: `⚠️ **Connection Error**: Unable to reach Credence API. Please verify the backend server is running.\n\n*Error details: ${error.message}*`,
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

  // Check if routed with query parameters
  if (route.query.q) {
    if (route.query.category) {
      updateCurrentProfile({
        ...activeSession.value.profile,
        category: route.query.category
      })
    }
    inputQuery.value = String(route.query.q)
    submitQuery()
  }
})
</script>
