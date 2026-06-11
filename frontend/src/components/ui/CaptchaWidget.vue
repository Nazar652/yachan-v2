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
    <label class="text-[13px] font-bold">Captcha</label>

    <div class="flex items-center gap-3">
      <div class="flex h-14 w-36 items-center justify-center rounded-field border border-border bg-surface-2">
        <span v-if="isPending" class="text-xs text-text-muted">Loading…</span>
        <span v-else-if="isError" class="text-xs text-danger">Failed</span>
        <img
          v-else-if="captcha"
          :src="`data:image/png;base64,${captcha.image_base64}`"
          alt="captcha"
          class="max-h-12 max-w-full"
        />
      </div>

      <BaseButton type="button" variant="link" size="sm" @click="emit('refresh')">
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

