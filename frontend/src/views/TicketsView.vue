<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { listTickets } from '../api/client'
import type { Ticket, TicketPriority, TicketStatus } from '../api/types'
import StatusBadge from '../components/StatusBadge.vue'
import TicketForm from '../components/TicketForm.vue'

const PAGE_SIZE = 10

const items = ref<Ticket[]>([])
const total = ref(0)
const page = ref(1)
const status = ref<TicketStatus | ''>('')
const priority = ref<TicketPriority | ''>('')
const loading = ref(false)
const error = ref('')
const showForm = ref(false)

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / PAGE_SIZE)))

async function load(): Promise<void> {
  loading.value = true
  error.value = ''
  try {
    const result = await listTickets({
      status: status.value,
      priority: priority.value,
      page: page.value,
      page_size: PAGE_SIZE,
    })
    items.value = result.items
    total.value = result.total
  } catch (err) {
    error.value = err instanceof Error ? err.message : '加载失败'
    items.value = []
  } finally {
    loading.value = false
  }
}

watch([status, priority], () => {
  if (page.value !== 1) {
    page.value = 1
    return
  }
  void load()
})

watch(page, () => {
  void load()
})

onMounted(() => {
  void load()
})

function onCreated(): void {
  showForm.value = false
  status.value = ''
  priority.value = ''
  page.value = 1
  void load()
}

function formatTime(value: string): string {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString('zh-CN', { hour12: false })
}
</script>

<template>
  <div>
    <div class="row" style="margin-bottom: 16px">
      <h2 style="margin: 0">我的工单</h2>
      <span class="muted">共 {{ total }} 条</span>
      <div class="spacer" />
      <button type="button" class="primary" @click="showForm = !showForm">
        {{ showForm ? '收起' : '+ 新建工单' }}
      </button>
    </div>

    <TicketForm v-if="showForm" @created="onCreated" @cancel="showForm = false" />

    <div class="panel" style="margin-top: 16px">
      <div class="row" style="margin-bottom: 14px">
        <div style="width: 150px">
          <label for="filter-status">状态</label>
          <select id="filter-status" v-model="status">
            <option value="">全部</option>
            <option value="open">待处理</option>
            <option value="in_progress">处理中</option>
            <option value="done">已完成</option>
          </select>
        </div>
        <div style="width: 150px">
          <label for="filter-priority">优先级</label>
          <select id="filter-priority" v-model="priority">
            <option value="">全部</option>
            <option value="low">低</option>
            <option value="medium">中</option>
            <option value="high">高</option>
          </select>
        </div>
        <div class="spacer" />
        <button type="button" :disabled="loading" @click="load">
          {{ loading ? '加载中…' : '刷新' }}
        </button>
      </div>

      <div v-if="error" class="error-box">{{ error }}</div>

      <table v-if="items.length" class="tickets">
        <thead>
          <tr>
            <th style="width: 32%">标题 / AI 摘要</th>
            <th>状态</th>
            <th>优先级</th>
            <th>分类</th>
            <th>创建时间</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="ticket in items" :key="ticket.id">
            <td>
              <router-link class="ticket-title" :to="{ name: 'ticket-detail', params: { id: ticket.id } }">
                #{{ ticket.id }} {{ ticket.title }}
              </router-link>
              <div class="muted" style="margin-top: 4px">
                {{ ticket.summary || '（无摘要）' }}
              </div>
            </td>
            <td><StatusBadge kind="status" :value="ticket.status" /></td>
            <td><StatusBadge kind="priority" :value="ticket.priority" /></td>
            <td>
              <StatusBadge kind="category" :value="ticket.category" />
              <div v-if="ticket.ai_status === 'failed'" class="badge ai-failed" style="margin-top: 4px">
                AI 降级
              </div>
            </td>
            <td class="muted">{{ formatTime(ticket.created_at) }}</td>
          </tr>
        </tbody>
      </table>

      <div v-else class="empty">
        {{ loading ? '加载中…' : '还没有工单，点右上角「新建工单」试试' }}
      </div>

      <div class="pager">
        <span>第 {{ page }} / {{ totalPages }} 页</span>
        <button type="button" :disabled="page <= 1 || loading" @click="page -= 1">上一页</button>
        <button type="button" :disabled="page >= totalPages || loading" @click="page += 1">下一页</button>
      </div>
    </div>
  </div>
</template>
