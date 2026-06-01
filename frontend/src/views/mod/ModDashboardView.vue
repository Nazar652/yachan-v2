<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useQueryClient } from '@tanstack/vue-query'

import { useAuthStore } from '@/stores/auth'
import { useReports, reportsQueryKey } from '@/composables/useReports'
import { resolveReport } from '@/api/mod'
import BaseButton from '@/components/ui/BaseButton.vue'

const router = useRouter()
const auth = useAuthStore()
const queryClient = useQueryClient()

const { data: reports, isPending, isError } = useReports()

const resolvingId = ref<number | null>(null)

async function onResolve(id: number) {
  resolvingId.value = id
  try {
    await resolveReport(id)
    await queryClient.invalidateQueries({ queryKey: reportsQueryKey })
  } finally {
    resolvingId.value = null
  }
}

async function onLogout() {
  auth.logout()
  await router.push('/mod/login')
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString()
}
</script>

<template>
  <div class="max-w-3xl mx-auto px-4 py-6">
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-xl font-semibold">Mod dashboard</h1>
      <BaseButton variant="ghost" size="sm" @click="onLogout">Log out</BaseButton>
    </div>

    <h2 class="text-lg font-medium mb-3">Reports</h2>

    <p v-if="isPending" class="text-secondary">Loading…</p>
    <p v-else-if="isError" class="text-red-500">Failed to load reports.</p>
    <p v-else-if="!reports?.length" class="text-secondary">No reports.</p>

    <ul v-else class="flex flex-col gap-2">
      <li
        v-for="report in reports"
        :key="report.id"
        class="flex items-center gap-3 border border-border rounded p-3 text-sm"
      >
        <span class="font-mono text-secondary">#{{ report.id }}</span>
        <span class="font-mono">post {{ report.post_id }}</span>
        <span class="flex-1 truncate">{{ report.reason ?? '(no reason)' }}</span>
        <span class="text-secondary">{{ formatDate(report.created_at) }}</span>
        <span v-if="report.is_resolved" class="text-secondary italic">resolved</span>
        <BaseButton
          v-else
          variant="primary"
          size="sm"
          :disabled="resolvingId === report.id"
          @click="onResolve(report.id)"
        >
          {{ resolvingId === report.id ? '…' : 'Resolve' }}
        </BaseButton>
      </li>
    </ul>
  </div>
</template>
