<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  page: number
  total: number
}>()

const emit = defineEmits<{
  'update:page': [page: number]
}>()

// windowed pages: edges + neighbours of the current page, gaps collapse to ···
const shownPages = computed(() => {
  const wanted = new Set([1, 2, props.total - 1, props.total, props.page - 1, props.page, props.page + 1])
  return [...wanted].filter((page) => page >= 1 && page <= props.total).sort((a, b) => a - b)
})

function go(page: number) {
  const clamped = Math.min(props.total, Math.max(1, page))

  if (clamped !== props.page) emit('update:page', clamped)
}
</script>

<template>
  <nav v-if="total > 1" class="my-8 flex flex-wrap items-center justify-center gap-1.5">
    <button
      type="button"
      class="inline-flex h-9 cursor-pointer items-center justify-center gap-1 rounded-field border border-border bg-surface px-3 text-[13px] font-semibold text-text transition-colors enabled:hover:border-gold enabled:hover:bg-surface-3 enabled:hover:text-accent disabled:cursor-default disabled:opacity-40"
      :disabled="page === 1"
      @click="go(page - 1)"
    >
      ‹ Prev
    </button>

    <template v-for="(shownPage, index) in shownPages" :key="shownPage">
      <span
        v-if="index > 0 && shownPage - shownPages[index - 1]! > 1"
        class="select-none px-1 font-mono text-[13px] tracking-widest text-text-muted"
      >
        ···
      </span>
      <button
        type="button"
        class="inline-flex h-9 min-w-9 cursor-pointer items-center justify-center rounded-field border px-2 font-mono text-[13px] transition-colors"
        :class="
          shownPage === page
            ? 'border-gold bg-gold font-bold text-on-gold shadow-card'
            : 'border-border bg-surface text-text hover:border-gold hover:bg-surface-3 hover:text-accent'
        "
        @click="go(shownPage)"
      >
        {{ shownPage }}
      </button>
    </template>

    <button
      type="button"
      class="inline-flex h-9 cursor-pointer items-center justify-center gap-1 rounded-field border border-border bg-surface px-3 text-[13px] font-semibold text-text transition-colors enabled:hover:border-gold enabled:hover:bg-surface-3 enabled:hover:text-accent disabled:cursor-default disabled:opacity-40"
      :disabled="page === total"
      @click="go(page + 1)"
    >
      Next ›
    </button>
  </nav>
</template>
