<script setup lang="ts">
import { computed } from 'vue'
import { tv, type VariantProps } from 'tailwind-variants'

// the button's look lives here only; pages use <BaseButton variant="..."> and
// never repeat tailwind classes. colors come from design tokens (bg-gold etc.)
const button = tv({
  base: 'inline-flex items-center justify-center gap-1.5 whitespace-nowrap rounded-field border border-transparent font-bold transition-all cursor-pointer disabled:cursor-not-allowed disabled:opacity-50',
  variants: {
    variant: {
      primary:
        'bg-gold text-on-gold shadow-card hover:-translate-y-px hover:shadow-pop hover:brightness-95 active:translate-y-0',
      ghost: 'border-border bg-transparent text-text hover:border-gold hover:bg-surface-3',
      danger: 'bg-danger text-white hover:bg-danger-hover',
      link: 'border-none bg-transparent font-semibold text-accent hover:text-accent-hover hover:underline',
    },
    size: {
      sm: 'px-2.5 py-1 text-[12.5px]',
      md: 'px-[18px] py-2 text-sm',
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
