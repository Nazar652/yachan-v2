<script setup lang="ts">
import { computed } from 'vue'

import { numberCodeLines } from '@/utils/postHtml'

// server-rendered post html (markup already sanitised on the backend); we only
// add per-line wrappers so code blocks get gutter line numbers via css counters
const props = defineProps<{ html: string }>()

const emit = defineEmits<{ navigate: [postNumber: number] }>()

const rendered = computed(() => numberCodeLines(props.html))

// the >>N references render as <a class="post-ref" data-post="N"> via v-html, so
// vue can't bind @click to them directly — delegate from the wrapper instead
function onClick(event: MouseEvent) {
  const ref = (event.target as HTMLElement).closest<HTMLElement>('a.post-ref[data-post]')
  if (!ref) return
  event.preventDefault()
  emit('navigate', Number(ref.dataset.post))
}
</script>

<template>
  <div class="post-body" v-html="rendered" @click="onClick" />
</template>
