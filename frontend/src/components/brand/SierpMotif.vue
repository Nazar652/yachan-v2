<script setup lang="ts">
import { computed } from 'vue'

// downward sierpinski-triangle motif used as a decorative divider mark
const props = withDefaults(defineProps<{ size?: number; color?: string }>(), {
  size: 20,
  color: 'currentColor',
})

const TRIANGLE_CENTERS: Array<[number, number]> = [
  [0.3, 0.28],
  [0.5, 0.28],
  [0.7, 0.28],
  [0.4, 0.52],
  [0.6, 0.52],
  [0.5, 0.76],
]

const triangles = computed(() => {
  const radius = props.size / 8
  const height = radius * 0.866
  return TRIANGLE_CENTERS.map(([x, y]) => {
    const centerX = x * props.size
    const centerY = y * props.size
    return `${centerX},${centerY + height} ${centerX - radius},${centerY - height * 0.5} ${centerX + radius},${centerY - height * 0.5}`
  })
})
</script>

<template>
  <svg :viewBox="`0 0 ${size} ${size}`" :width="size" :height="size" aria-hidden="true">
    <g :fill="color">
      <polygon v-for="(points, index) in triangles" :key="index" :points="points" />
    </g>
  </svg>
</template>
