import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import StatusBadge from '../StatusBadge.vue'

describe('StatusBadge', () => {
  it('把状态码翻译成中文', () => {
    const wrapper = mount(StatusBadge, { props: { kind: 'status', value: 'in_progress' } })
    expect(wrapper.text()).toBe('处理中')
    expect(wrapper.classes()).toContain('status-in_progress')
  })

  it('分类统一使用 category 样式，不按值分色', () => {
    const wrapper = mount(StatusBadge, { props: { kind: 'category', value: 'bug' } })
    expect(wrapper.text()).toBe('缺陷')
    expect(wrapper.classes()).toContain('category')
    expect(wrapper.classes()).not.toContain('category-bug')
  })

  it('未知值原样展示，不抛错', () => {
    const wrapper = mount(StatusBadge, { props: { kind: 'priority', value: 'unknown' } })
    expect(wrapper.text()).toBe('unknown')
  })
})
