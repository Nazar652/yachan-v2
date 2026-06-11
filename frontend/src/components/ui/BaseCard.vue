<script setup lang="ts">
import { tv, type VariantProps } from 'tailwind-variants'

// reusable card shell — pages compose content inside, never repeat border/bg classes
const card = tv({
  base: 'rounded-card border border-border bg-surface p-4 shadow-card',
  variants: {
    interactive: {
      true: 'transition-all hover:-translate-y-0.5 hover:border-gold hover:shadow-pop',
    },
  },
  defaultVariants: { interactive: false },
})

type CardVariants = VariantProps<typeof card>

const props = withDefaults(
  defineProps<{ interactive?: CardVariants['interactive'] }>(),
  { interactive: false },
)
</script>

<template>
  <div :class="card({ interactive: props.interactive })">
    <slot />
  </div>
</template>
