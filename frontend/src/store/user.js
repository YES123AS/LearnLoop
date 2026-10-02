import { defineStore } from 'pinia'

const STORAGE_KEY = 'sc_user_session'

const ROLE_HOME = {
  student: '/dashboard',
  teacher: '/teacher/dashboard',
  parent: '/parent/dashboard'
}

const ROLE_LABEL = {
  student: '学生',
  teacher: '教师',
  parent: '家长'
}

const MOCK_USERS = {
  student: { username: 'student', password: '123456', role: 'student', name: '学生用户' },
  teacher: { username: 'teacher', password: '123456', role: 'teacher', name: '教师用户' },
  parent: { username: 'parent', password: '123456', role: 'parent', name: '家长用户' }
}

function safeParse(raw) {
  try {
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

export const useUserStore = defineStore('user', {
  state: () => ({
    userInfo: null,
    role: '',
    token: '',
    isLoggedIn: false
  }),
  getters: {
    roleLabel: (state) => ROLE_LABEL[state.role] || '未登录',
    homePath: (state) => ROLE_HOME[state.role] || '/login'
  },
  actions: {
    restoreLogin() {
      const data = safeParse(localStorage.getItem(STORAGE_KEY))
      if (!data?.token || !data?.role) return false
      this.userInfo = data.userInfo || null
      this.role = data.role
      this.token = data.token
      this.isLoggedIn = true
      return true
    },
    login({ username, password, role }) {
      const account = MOCK_USERS[role]
      if (!account || account.username !== username || account.password !== password || account.role !== role) {
        throw new Error('账号、密码或身份不正确')
      }
      this.userInfo = { username: account.username, name: account.name, role: account.role }
      this.role = account.role
      this.token = `mock-token-${account.role}-${Date.now()}`
      this.isLoggedIn = true
      localStorage.setItem(STORAGE_KEY, JSON.stringify({ userInfo: this.userInfo, role: this.role, token: this.token }))
      return this.userInfo
    },
    logout() {
      this.userInfo = null
      this.role = ''
      this.token = ''
      this.isLoggedIn = false
      localStorage.removeItem(STORAGE_KEY)
    },
    hasRole(roles = []) {
      return this.isLoggedIn && roles.includes(this.role)
    },
    canAccessRoute(route) {
      const roles = route?.meta?.roles
      if (!roles || !roles.length) return true
      if (!this.isLoggedIn) return false
      return roles.includes(this.role)
    },
    getHomeByRole(role = this.role) {
      return ROLE_HOME[role] || '/login'
    }
  }
})
