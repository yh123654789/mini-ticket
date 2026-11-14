<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { login } from '../api/client'
import { useAuth } from '../stores/auth'

const email = ref('alice@example.com')
const password = ref('alice123')
const error = ref('')
const loading = ref(false)

const router = useRouter()
const route = useRoute()
const { applySession } = useAuth()

async function submit(): Promise<void> {
  error.value = ''
  loading.value = true
  try {
    const result = await login(email.value.trim(), password.value)
    applySession(result.access_token, result.user)
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/tickets'
    await router.replace(redirect)
  } catch (err) {
    error.value = err instanceof Error ? err.message : '登录失败'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="panel" style="max-width: 420px; margin: 6vh auto 0">
    <h2 style="margin-top: 0">登录 Mini Ticket</h2>
    <p class="muted" style="margin-top: -6px">内部工单系统 · AI 自动摘要与分类</p>

    <div v-if="error" class="error-box">{{ error }}</div>

    <form class="form-grid" @submit.prevent="submit">
      <div>
        <label for="email">邮箱</label>
        <input id="email" v-model="email" type="email" autocomplete="username" />
      </div>
      <div>
        <label for="password">密码</label>
        <input id="password" v-model="password" type="password" autocomplete="current-password" />
      </div>
      <button type="submit" class="primary" :disabled="loading">
        {{ loading ? '登录中…' : '登录' }}
      </button>
    </form>

    <p class="muted" style="margin-bottom: 0">
      演示账号：alice@example.com / alice123 &nbsp;·&nbsp; bob@example.com / bob123
    </p>
  </div>
</template>
