<script setup lang="ts">
import { ref } from 'vue'
import { createTicket } from '../api/client'
import type { Ticket, TicketPriority } from '../api/types'

const emit = defineEmits<{ created: [ticket: Ticket]; cancel: [] }>()

const title = ref('')
const description = ref('')
const priority = ref<TicketPriority>('medium')
const submitting = ref(false)
const error = ref('')

async function submit(): Promise<void> {
  error.value = ''

  if (!title.value.trim() || !description.value.trim()) {
    error.value = '标题和描述都不能为空'
    return
  }

  submitting.value = true
  try {
    const ticket = await createTicket({
      title: title.value.trim(),
      description: description.value.trim(),
      priority: priority.value,
    })
    title.value = ''
    description.value = ''
    priority.value = 'medium'
    emit('created', ticket)
  } catch (err) {
    error.value = err instanceof Error ? err.message : '创建失败'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <form class="panel" @submit.prevent="submit">
    <h3 style="margin-top: 0">新建工单</h3>

    <div v-if="error" class="error-box">{{ error }}</div>

    <div class="form-grid">
      <div>
        <label for="ticket-title">标题</label>
        <input id="ticket-title" v-model="title" maxlength="200" placeholder="一句话说清问题" />
      </div>

      <div>
        <label for="ticket-description">描述</label>
        <textarea
          id="ticket-description"
          v-model="description"
          rows="4"
          maxlength="4000"
          placeholder="复现步骤、期望结果、实际结果……"
        />
      </div>

      <div>
        <label for="ticket-priority">优先级</label>
        <select id="ticket-priority" v-model="priority">
          <option value="low">低</option>
          <option value="medium">中</option>
          <option value="high">高</option>
        </select>
      </div>
    </div>

    <div class="row" style="margin-top: 16px">
      <button type="submit" class="primary" :disabled="submitting">
        {{ submitting ? '提交中…' : '提交（AI 自动摘要）' }}
      </button>
      <button type="button" @click="emit('cancel')">取消</button>
    </div>
  </form>
</template>
