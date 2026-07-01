<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { modLogin } from '@/api/mod'
import { useAuthStore } from '@/stores/auth'
import BaseButton from '@/components/ui/BaseButton.vue'
import BaseInput from '@/components/ui/BaseInput.vue'
import MonogramSeal from '@/components/brand/MonogramSeal.vue'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const username = ref('')
const password = ref('')
const isSubmitting = ref(false)
const error = ref<string | null>(
  route.query.sessionExpired ? 'Your session has expired. Please sign in again.' : null,
)

async function onSubmit() {
  error.value = null

  if (!username.value || !password.value) {
    error.value = 'Enter username and password.'
    return
  }

  isSubmitting.value = true
  try {
    const token = await modLogin(username.value, password.value)
    auth.login(token.access_token, token.role)
    await router.push('/mod')
  } catch (err: unknown) {
    const detail = (err as Record<string, unknown>)?.detail
    error.value = typeof detail === 'string' ? detail : 'Login failed.'
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <div class="mx-auto my-14 max-w-[380px]">
    <div class="mb-5 grid place-items-center">
      <MonogramSeal :size="92" />
    </div>

    <form
      class="flex flex-col gap-4 rounded-card border border-border bg-surface p-6 shadow-card"
      @submit.prevent="onSubmit"
    >
      <h1 class="text-center text-2xl font-extrabold">Mod login</h1>

      <div class="flex flex-col gap-1.5">
        <label for="mod-username" class="text-[13px] font-bold">Username</label>
        <BaseInput id="mod-username" v-model="username" autocomplete="username" />
      </div>

      <div class="flex flex-col gap-1.5">
        <label for="mod-password" class="text-[13px] font-bold">Password</label>
        <BaseInput
          id="mod-password"
          v-model="password"
          type="password"
          autocomplete="current-password"
        />
      </div>

      <p v-if="error" class="text-sm text-danger">{{ error }}</p>

      <BaseButton type="submit" variant="primary" class="mt-1 w-full" :disabled="isSubmitting">
        {{ isSubmitting ? 'Signing in…' : 'Sign in' }}
      </BaseButton>
    </form>
  </div>
</template>
