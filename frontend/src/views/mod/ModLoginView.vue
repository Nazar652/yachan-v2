<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

import { modLogin } from '@/api/mod'
import { useAuthStore } from '@/stores/auth'
import BaseButton from '@/components/ui/BaseButton.vue'
import BaseInput from '@/components/ui/BaseInput.vue'

const router = useRouter()
const auth = useAuthStore()

const username = ref('')
const password = ref('')
const isSubmitting = ref(false)
const error = ref<string | null>(null)

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
  <div class="max-w-sm mx-auto px-4 py-10">
    <h1 class="text-xl font-semibold mb-6">Mod login</h1>

    <form class="flex flex-col gap-4" @submit.prevent="onSubmit">
      <div class="flex flex-col gap-1">
        <label for="mod-username" class="text-sm font-medium">Username</label>
        <BaseInput id="mod-username" v-model="username" autocomplete="username" />
      </div>

      <div class="flex flex-col gap-1">
        <label for="mod-password" class="text-sm font-medium">Password</label>
        <BaseInput
          id="mod-password"
          v-model="password"
          type="password"
          autocomplete="current-password"
        />
      </div>

      <p v-if="error" class="text-sm text-red-500">{{ error }}</p>

      <BaseButton type="submit" variant="primary" :disabled="isSubmitting">
        {{ isSubmitting ? 'Signing in…' : 'Sign in' }}
      </BaseButton>
    </form>
  </div>
</template>
