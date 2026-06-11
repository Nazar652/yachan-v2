<script setup lang="ts">
import { nextTick, ref } from 'vue'

import { applyFormat, type TextFormat } from '@/utils/formatting'
import BaseButton from '@/components/ui/BaseButton.vue'

// passthrough attributes (id, rows, placeholder…) belong on the textarea,
// not on the wrapping div
defineOptions({ inheritAttrs: false })

const model = defineModel<string>({ default: '' })

interface ToolbarButton {
  format: TextFormat
  label: string
  title: string
  labelClass?: string
}

const toolbarButtons: ToolbarButton[] = [
  { format: 'bold', label: 'B', title: 'Bold', labelClass: 'font-bold' },
  { format: 'italic', label: 'i', title: 'Italic', labelClass: 'italic' },
  { format: 'underline', label: 'u', title: 'Underline', labelClass: 'underline' },
  { format: 'strike', label: 'S', title: 'Strikethrough', labelClass: 'line-through' },
  { format: 'spoiler', label: '▆', title: 'Spoiler' },
  { format: 'inline-code', label: 'C', title: 'Inline code', labelClass: 'font-mono' },
  { format: 'code-block', label: '{ }', title: 'Code block', labelClass: 'font-mono' },
  { format: 'quote', label: '>', title: 'Quote', labelClass: 'font-mono' },
  { format: 'escape', label: '\\', title: 'Escape markdown', labelClass: 'font-mono' },
]

const bodyTextarea = ref<HTMLTextAreaElement | null>(null)
const refusalReason = ref<string | null>(null)

async function onFormat(format: TextFormat) {
  const textarea = bodyTextarea.value
  if (!textarea) return

  const outcome = applyFormat(model.value, textarea.selectionStart, textarea.selectionEnd, format)
  if (!outcome.applied) {
    refusalReason.value = outcome.reason
    return
  }

  refusalReason.value = null
  model.value = outcome.text
  await nextTick()
  textarea.focus()
  textarea.setSelectionRange(outcome.selectionStart, outcome.selectionEnd)
}
</script>

<template>
  <div class="flex flex-col gap-1">
    <div class="flex flex-wrap gap-1">
      <BaseButton
        v-for="toolbarButton in toolbarButtons"
        :key="toolbarButton.format"
        variant="ghost"
        size="sm"
        :title="toolbarButton.title"
        @mousedown.prevent
        @click="onFormat(toolbarButton.format)"
      >
        <span class="inline-block min-w-4 text-center" :class="toolbarButton.labelClass">{{ toolbarButton.label }}</span>
      </BaseButton>
    </div>

    <textarea
      ref="bodyTextarea"
      v-model="model"
      v-bind="$attrs"
      class="min-h-32 w-full resize-y rounded-field border border-border bg-bg px-3 py-2 text-sm text-text outline-none transition-colors placeholder:text-text-muted focus:border-gold focus:ring-[3px] focus:ring-gold/25"
      @input="refusalReason = null"
    />

    <p v-if="refusalReason" class="text-xs text-text-muted">{{ refusalReason }}</p>
  </div>
</template>
