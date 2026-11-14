import { computed, ref } from 'vue'
import { fetchMe } from '../api/client'
import { setToken, token } from '../api/session'
import type { User } from '../api/types'

// 模块级单例：整个应用共享同一份登录态
const currentUser = ref<User | null>(null)

export function useAuth() {
  const isLoggedIn = computed(() => Boolean(token.value))

  function applySession(accessToken: string, user: User): void {
    setToken(accessToken)
    currentUser.value = user
  }

  function logout(): void {
    setToken(null)
    currentUser.value = null
  }

  /** 刷新页面后用已存的 token 恢复用户信息；失败说明 token 失效，直接清掉。 */
  async function restore(): Promise<void> {
    if (!token.value || currentUser.value) return
    try {
      currentUser.value = await fetchMe()
    } catch {
      logout()
    }
  }

  return {
    user: computed(() => currentUser.value),
    isLoggedIn,
    applySession,
    logout,
    restore,
  }
}
