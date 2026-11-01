import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import router from './router'
import { useAuth } from './auth'

const app = createApp(App)
app.use(router)

// Initialize and validate persisted authentication token
const auth = useAuth()
auth.checkAuth()

app.mount('#app')
