<script setup lang="ts">
import { tv } from 'tailwind-variants'

const input = tv({
  base: 'w-full rounded-field border border-border bg-bg px-3 py-2 text-sm text-text outline-none transition-colors placeholder:text-text-muted focus:border-gold focus:ring-[3px] focus:ring-gold/25',
})

const model = defineModel<string>({ default: '' })

withDefaults(defineProps<{ type?: string; placeholder?: string }>(), { type: 'text' })
</script>

<template>
  <input v-model="model" :type="type" :placeholder="placeholder" :class="input()" />
</template>
