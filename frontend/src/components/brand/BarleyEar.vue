<script setup lang="ts">
import { computed } from 'vue'

// paths are generated from grain anchors so the mark stays crisp at any size
const props = withDefaults(
  defineProps<{ height?: number; amber?: string; gold?: string }>(),
  { height: 36, amber: 'var(--color-gold-2)', gold: 'var(--color-gold)' },
)

const GRAIN_ANCHORS: Array<[number, number]> = [
  [218, 17],
  [196, 21],
  [174, 23],
  [152, 23],
  [130, 21],
  [108, 17],
]

const grainPaths = computed(() => {
  const paths: string[] = []
  for (const [y, dx] of GRAIN_ANCHORS) {
    paths.push(
      `M50,${y} Q${50 + dx * 0.5},${y - 20} ${50 + dx},${y - 19} Q${50 + dx * 0.55},${y - 5} 50,${y + 5} Z`,
    )
    paths.push(
      `M50,${y} Q${50 - dx * 0.5},${y - 20} ${50 - dx},${y - 19} Q${50 - dx * 0.55},${y - 5} 50,${y + 5} Z`,
    )
  }
  return paths
})

const width = computed(() => (props.height * 100) / 300)
</script>

<template>
  <svg viewBox="0 0 100 300" :height="height" :width="width" aria-hidden="true">
    <path d="M50,224 L50,96" fill="none" :stroke="amber" stroke-width="4" stroke-linecap="round" />
    <g :stroke="amber" stroke-width="3.2" stroke-linejoin="round" :fill="gold">
      <path d="M50,98 Q44,80 50,62 Q56,80 50,98 Z" />
      <path v-for="(grain, index) in grainPaths" :key="index" :d="grain" />
    </g>
    <g :stroke="amber" stroke-width="3.4" stroke-linecap="round" fill="none">
      <path d="M50,70 L50,22" />
      <path d="M50,74 L37,30" />
      <path d="M50,74 L63,30" />
      <path d="M50,72 L44,26" />
      <path d="M50,72 L56,26" />
    </g>
    <path d="M50,226 L50,292" fill="none" :stroke="amber" stroke-width="5.5" stroke-linecap="round" />
    <path d="M47,232 L47,286" fill="none" :stroke="gold" stroke-width="1.6" stroke-linecap="round" />
  </svg>
</template>
