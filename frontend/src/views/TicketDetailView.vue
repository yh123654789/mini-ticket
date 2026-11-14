<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { getTicket, updateTicketStatus } from '../api/client'
import type { Ticket, TicketStatus } from '../api/types'
import StatusBadge from '../components/StatusBadge.vue'

const props = defineProps<{ id: string }>()

const ticket = ref<Ticket | null>(null)
const loading = ref(true)
const saving = ref(false)
const error = ref('')

const STATUS_OPTIONS: { value: TicketStatus; label: string }[] = [
  { value: 'open', label: '待处理' },
  { value: 'in_progress', label: '处理中' },
  { value: 'done', label: '已完成' },
]

async function load(): Promise<void> {
  loading.value = true
  error.value = ''
  try {
    ticket.value = await getTicket(Number(props.id))
  } catch (err) {
    error.value = err instanceof Error ? err.message : '加载失败'
    ticket.value = null
  } finally {
    loading.value = false
  }
}

async function changeStatus(next: TicketStatus): Promise<void> {
  if (!ticket.value || ticket.value.status === next) return
  saving.value = true
  error.value = ''
  try {
    ticket.value = await updateTicketStatus(ticket.value.id, next)
  } catch (err) {
    error.value = err instanceof Error ? err.message : '状态更新失败'
  } finally {
    saving.value = false
  }
}

function formatTime(value: string): string {
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString('zh-CN', { hour12: false })
}

onMounted(() => {
  void load()
})
</script>

<template>
  <div>
    <div class="row" style="margin-bottom: 14px">
      <router-link :to="{ name: 'tickets' }">← 返回列表</router-link>
      <div class="spacer" />
      <button type="button" :disabled="loading" @click="load">刷新</button>
    </div>

    <div v-if="error" class="error-box">{{ error }}</div>

    <div v-if="ticket" class="panel">
      <h2 style="margin: 0 0 6px">#{{ ticket.id }} {{ ticket.title }}</h2>

      <div class="detail-meta">
        <StatusBadge kind="status" :value="ticket.status" />
        <StatusBadge kind="priority" :value="ticket.priority" />
        <StatusBadge kind="category" :value="ticket.category" />
        <span v-if="ticket.ai_status === 'failed'" class="badge ai-failed">AI 降级</span>
        <span class="muted">创建于 {{ formatTime(ticket.created_at) }}</span>
      </div>

      <div class="ai-box" style="margin-bottom: 16px">
        <div class="muted" style="margin-bottom: 6px">AI 摘要</div>
        <div>{{ ticket.summary || '（无摘要）' }}</div>
        <div v-if="ticket.ai_status === 'failed'" class="muted" style="margin-top: 6px">
          本次 AI 分析失败，摘要已退化为原文截断，分类记为「其他」，工单未受影响。
        </div>
      </div>

      <div class="muted" style="margin-bottom: 6px">描述</div>
      <div class="detail-body">{{ ticket.description }}</div>

      <div style="margin-top: 20px">
        <div class="muted" style="margin-bottom: 8px">更新状态</div>
        <div class="status-actions">
          <button
            v-for="option in STATUS_OPTIONS"
            :key="option.value"
            type="button"
            :class="{ primary: ticket.status === option.value }"
            :disabled="saving || ticket.status === option.value"
            @click="changeStatus(option.value)"
          >
            {{ option.label }}
          </button>
        </div>
      </div>
    </div>

    <div v-else-if="loading" class="panel empty">加载中…</div>
    <div v-else class="panel empty">工单不存在，或你没有权限查看</div>
  </div>
</template>
