import { ref } from 'vue'

const TOKEN_KEY = 'mini-ticket-token'

// 用 ref 保存，模板里能跟着响应式更新
export const token = ref<string | null>(localStorage.getItem(TOKEN_KEY))

export function getToken(): string | null {
  return token.value
}

export function setToken(value: string | null): void {
  token.value = value
  if (value) {
    localStorage.setItem(TOKEN_KEY, value)
  } else {
    localStorage.removeItem(TOKEN_KEY)
  }
}
