<script setup lang="ts">
import { computed } from 'vue'

import { numberCodeLines } from '@/utils/postHtml'

// server-rendered post html (markup already sanitised on the backend); we only
// add per-line wrappers so code blocks get gutter line numbers via css counters
const props = defineProps<{ html: string }>()

const rendered = computed(() => numberCodeLines(props.html))
</script>

<template>
  <div class="post-body" v-html="rendered" />
</template>
