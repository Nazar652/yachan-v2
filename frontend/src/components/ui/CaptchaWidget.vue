<script setup lang="ts">
import { computed } from 'vue'
import type { CaptchaChallengeResponse } from '@/api/types'
import { useTheme } from '@/composables/useTheme'
import BaseButton from '@/components/ui/BaseButton.vue'
import BaseInput from '@/components/ui/BaseInput.vue'

const props = defineProps<{
  captcha: CaptchaChallengeResponse | undefined
  isPending: boolean
  isError: boolean
}>()

const answer = defineModel<string>({ default: '' })

const emit = defineEmits<{
  refresh: []
}>()

const { theme } = useTheme()

// the server renders both theme variants for the same answer, so switching
// theme swaps the displayed image instantly without refetching the captcha
const imageBase64 = computed(() =>
  theme.value === 'dark' ? props.captcha?.image_base64_dark : props.captcha?.image_base64_light,
)
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
          :src="`data:image/png;base64,${imageBase64}`"
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

