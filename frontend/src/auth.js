import { ref, computed } from 'vue'

const tokenKey = 'credence_token'
const userKey = 'credence_user'

const token = ref(localStorage.getItem(tokenKey) || null)
const user = ref(null)

try {
  const savedUser = localStorage.getItem(userKey)
  if (savedUser) {
    user.value = JSON.parse(savedUser)
  }
} catch (e) {
  localStorage.removeItem(userKey)
}

export const useAuth = () => {
  const isAuthenticated = computed(() => !!token.value && !!user.value)

  const setAuth = (newToken, newUser) => {
    token.value = newToken
    user.value = newUser
    localStorage.setItem(tokenKey, newToken)
    localStorage.setItem(userKey, JSON.stringify(newUser))
  }

  const logout = () => {
    token.value = null
    user.value = null
    localStorage.removeItem(tokenKey)
    localStorage.removeItem(userKey)
  }

  const checkAuth = async () => {
    if (!token.value) return null
    try {
      const res = await fetch('/api/auth/me', {
        headers: {
          'Authorization': `Bearer ${token.value}`
        }
      })
      if (res.ok) {
        const data = await res.json()
        user.value = data
        localStorage.setItem(userKey, JSON.stringify(data))
        return data
      } else {
        // Token expired or invalid
        logout()
        return null
      }
    } catch (err) {
      console.warn('Auth check skipped (offline or network error):', err)
      return user.value
    }
  }

  const login = async (email, password) => {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    })
    const data = await res.json()
    if (!res.ok) {
      throw new Error(data.detail || 'Sign in failed. Please check your credentials.')
    }
    setAuth(data.token, data.user)
    return data
  }

  const register = async (name, email, password) => {
    const res = await fetch('/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, email, password })
    })
    const data = await res.json()
    if (!res.ok) {
      throw new Error(data.detail || 'Registration failed.')
    }
    setAuth(data.token, data.user)
    return data
  }

  const loginWithGoogle = async (credential) => {
    const res = await fetch('/api/auth/google', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ credential })
    })
    const data = await res.json()
    if (!res.ok) {
      throw new Error(data.detail || 'Google sign in failed.')
    }
    setAuth(data.token, data.user)
    return data
  }

  return {
    token,
    user,
    isAuthenticated,
    login,
    register,
    loginWithGoogle,
    logout,
    checkAuth
  }
}

