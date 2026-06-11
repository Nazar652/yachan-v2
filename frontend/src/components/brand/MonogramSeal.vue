<script setup lang="ts">
// hexagonal «Я» seal — the official mark of the mod zone (login, dashboard, capcode)
withDefaults(defineProps<{ size?: number; fg?: string; bg?: string }>(), {
  size: 110,
  fg: 'var(--color-gold)',
  bg: 'var(--color-ink)',
})
</script>

<template>
  <svg viewBox="0 0 120 120" :width="size" :height="size" aria-hidden="true">
    <path
      d="M60,4 L112,32 L112,88 L60,116 L8,88 L8,32 Z"
      :fill="bg"
      :stroke="fg"
      stroke-width="3"
      stroke-linejoin="round"
    />
    <text
      x="60"
      y="84"
      text-anchor="middle"
      font-family="var(--font-display)"
      font-weight="800"
      font-size="62"
      :fill="fg"
    >
      Я
    </text>
  </svg>
</template>
