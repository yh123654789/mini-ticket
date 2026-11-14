<script setup lang="ts">
import { computed } from 'vue'
import {
  CATEGORY_LABELS,
  PRIORITY_LABELS,
  STATUS_LABELS,
  type TicketCategory,
  type TicketPriority,
  type TicketStatus,
} from '../api/types'

const props = defineProps<{
  kind: 'status' | 'priority' | 'category'
  value: string
}>()

const label = computed(() => {
  if (props.kind === 'status') {
    return STATUS_LABELS[props.value as TicketStatus] ?? props.value
  }
  if (props.kind === 'priority') {
    return PRIORITY_LABELS[props.value as TicketPriority] ?? props.value
  }
  return CATEGORY_LABELS[props.value as TicketCategory] ?? props.value
})

// 只有状态和优先级有区分色，分类统一用同一个紫色标签
const classes = computed(() =>
  props.kind === 'category' ? 'badge category' : `badge ${props.kind}-${props.value}`,
)
</script>

<template>
  <span :class="classes">{{ label }}</span>
</template>
