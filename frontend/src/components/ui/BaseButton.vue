<script setup lang="ts">
import { computed } from 'vue'
import { tv, type VariantProps } from 'tailwind-variants'

// the button's look lives here only; pages use <BaseButton variant="..."> and
// never repeat tailwind classes. colors come from design tokens (bg-accent etc.)
const button = tv({
  base: 'inline-flex items-center justify-center rounded font-medium transition cursor-pointer disabled:cursor-not-allowed disabled:opacity-50',
  variants: {
    variant: {
      primary: 'bg-accent text-white hover:bg-accent-hover',
      ghost: 'bg-transparent text-accent hover:bg-surface-2',
      danger: 'bg-danger text-white hover:opacity-90',
    },
    size: {
      sm: 'px-2 py-1 text-sm',
      md: 'px-4 py-2',
    },
  },
  defaultVariants: { variant: 'primary', size: 'md' },
})

type ButtonVariants = VariantProps<typeof button>

const props = withDefaults(
  defineProps<{
    variant?: ButtonVariants['variant']
    size?: ButtonVariants['size']
    type?: 'button' | 'submit'
    disabled?: boolean
  }>(),
  { type: 'button', disabled: false },
)

const classes = computed(() => button({ variant: props.variant, size: props.size }))
</script>

<template>
  <button :type="type" :disabled="disabled" :class="classes">
    <slot />
  </button>
</template>
