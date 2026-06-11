<script setup lang="ts">
import BarleyEar from '@/components/brand/BarleyEar.vue'
</script>

<template>
  <footer class="mt-14 border-t border-border py-8">
    <div class="mx-auto flex max-w-5xl flex-wrap items-center gap-4 px-4 text-[13px] text-text-muted">
      <BarleyEar :height="26" />
      <span class="font-display font-extrabold text-text">я<b class="text-gold-2">чан</b></span>
      <span class="font-mono text-xs uppercase tracking-[0.12em] text-accent">est. 2026</span>
      <span class="ml-auto inline-flex items-center gap-4">
        <a
          href="https://github.com/Nazar652/yachan-v2"
          target="_blank"
          rel="noopener"
          class="inline-flex items-center gap-1.5 font-semibold transition-colors hover:text-accent"
        >
          <svg viewBox="0 0 24 24" class="h-[15px] w-[15px]" fill="currentColor" aria-hidden="true">
            <path d="M12 2A10 10 0 0 0 8.84 21.5c.5.08.66-.22.66-.48v-1.7c-2.78.6-3.37-1.34-3.37-1.34-.45-1.16-1.1-1.47-1.1-1.47-.9-.62.07-.6.07-.6 1 .07 1.53 1.03 1.53 1.03.9 1.52 2.34 1.08 2.91.83.1-.65.35-1.08.63-1.33-2.22-.25-4.55-1.11-4.55-4.94 0-1.09.39-1.98 1.03-2.68-.1-.25-.45-1.27.1-2.65 0 0 .84-.27 2.75 1.02a9.6 9.6 0 0 1 5 0c1.91-1.29 2.75-1.02 2.75-1.02.55 1.38.2 2.4.1 2.65.64.7 1.03 1.59 1.03 2.68 0 3.84-2.34 4.69-4.57 4.94.36.31.68.92.68 1.85v2.74c0 .27.16.57.67.48A10 10 0 0 0 12 2z" />
          </svg>
          source
        </a>
        <span>made by nazariy von gerste</span>
      </span>
    </div>
  </footer>
</template>
