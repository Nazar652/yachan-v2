<script setup lang="ts">
import { tv } from 'tailwind-variants'

const input = tv({
  base: 'w-full rounded border border-border bg-surface px-2 py-1 text-text outline-none focus:border-accent',
})

const model = defineModel<string>({ default: '' })

withDefaults(defineProps<{ type?: string; placeholder?: string }>(), { type: 'text' })
</script>

<template>
  <input v-model="model" :type="type" :placeholder="placeholder" :class="input()" />
</template>
