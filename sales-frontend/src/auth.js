import { ref, computed } from 'vue'

const tokenKey = 'credence_sales_token'
const userKey = 'credence_sales_user'

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

export const useSalesAuth = () => {
  const isAuthenticated = computed(() => !!token.value && !!user.value)

  const isManager = computed(() => {
    const role = user.value?.role
    return role === 'SALES_MANAGER' || role === 'SALES_ADMIN' || role === 'SYSTEM_ADMIN'
  })

  const isAdmin = computed(() => {
    const role = user.value?.role
    return role === 'SALES_ADMIN' || role === 'SYSTEM_ADMIN'
  })

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
        if (data.role === 'CUSTOMER') {
          // Customers are not authorized for sales portal
          logout()
          return null
        }
        user.value = data
        localStorage.setItem(userKey, JSON.stringify(data))
        return data
      } else {
        logout()
        return null
      }
    } catch (err) {
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
      throw new Error(data.detail || 'Sign in failed.')
    }
    if (data.user?.role === 'CUSTOMER') {
      throw new Error('Access denied: Customer accounts cannot sign in to the Sales CRM.')
    }
    setAuth(data.token, data.user)
    return data
  }

  return {
    token,
    user,
    isAuthenticated,
    isManager,
    isAdmin,
    login,
    logout,
    checkAuth,
    setAuth
  }
}

