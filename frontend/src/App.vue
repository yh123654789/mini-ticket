<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from './stores/auth'

const { user, isLoggedIn, logout, restore } = useAuth()
const router = useRouter()

onMounted(() => {
  void restore()
})

function handleLogout(): void {
  logout()
  void router.push({ name: 'login' })
}
</script>

<template>
  <div class="app-shell">
    <header class="app-header">
      <div class="brand">Mini <span>Ticket</span></div>
      <div v-if="isLoggedIn" class="row">
        <span class="muted">{{ user?.name }}（{{ user?.email }}）</span>
        <button type="button" @click="handleLogout">退出登录</button>
      </div>
    </header>
    <main class="app-main">
      <router-view />
    </main>
  </div>
</template>
