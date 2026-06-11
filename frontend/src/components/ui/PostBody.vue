<script setup lang="ts">
import { computed } from 'vue'

import { annotateOwnRefs, numberCodeLines } from '@/utils/postHtml'

// server-rendered post html (markup already sanitised on the backend); we add
// per-line wrappers so code blocks get gutter line numbers via css counters, and
// tag references to the visitor's own posts with (You)
const props = withDefaults(
  defineProps<{ html: string; ownNumbers?: Set<number> }>(),
  { ownNumbers: () => new Set() },
)

const emit = defineEmits<{ navigate: [postNumber: number] }>()

const rendered = computed(() => numberCodeLines(annotateOwnRefs(props.html, props.ownNumbers)))

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
