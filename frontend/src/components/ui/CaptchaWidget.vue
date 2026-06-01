<script setup lang="ts">
import type { CaptchaChallengeResponse } from '@/api/types'
import BaseButton from '@/components/ui/BaseButton.vue'
import BaseInput from '@/components/ui/BaseInput.vue'

defineProps<{
  captcha: CaptchaChallengeResponse | undefined
  isPending: boolean
  isError: boolean
}>()

const answer = defineModel<string>({ default: '' })

const emit = defineEmits<{
  refresh: []
}>()
</script>

<template>
  <div class="flex flex-col gap-2">
    <label class="text-sm font-medium">Captcha</label>

    <div class="flex items-center gap-3">
      <div class="w-36 h-14 flex items-center justify-center rounded border border-border bg-surface">
        <span v-if="isPending" class="text-xs text-secondary">Loading…</span>
        <span v-else-if="isError" class="text-xs text-red-500">Failed</span>
        <img
          v-else-if="captcha"
          :src="`data:image/png;base64,${captcha.image_base64}`"
          alt="captcha"
          class="max-h-12 max-w-full"
        />
      </div>

      <BaseButton type="button" variant="ghost" size="sm" @click="emit('refresh')">
        ↺ Refresh
      </BaseButton>
    </div>

    <BaseInput
      v-model="answer"
      placeholder="Enter captcha answer"
      autocomplete="off"
    />
  </div>
</template>

