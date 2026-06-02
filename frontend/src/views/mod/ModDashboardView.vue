<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useQueryClient } from '@tanstack/vue-query'

import { useAuthStore } from '@/stores/auth'
import { useReports, reportsQueryKey } from '@/composables/useReports'
import { useBoards, boardsQueryKey } from '@/composables/useBoards'
import { resolveReport, createBoard, updateBoard } from '@/api/mod'
import type { BoardResponse } from '@/api/types'
import BaseButton from '@/components/ui/BaseButton.vue'
import BaseInput from '@/components/ui/BaseInput.vue'

const router = useRouter()
const auth = useAuthStore()
const queryClient = useQueryClient()

const { data: reports, isPending, isError } = useReports()
const { data: boards } = useBoards()

function errorDetail(error: unknown): string | null {
  const detail = (error as Record<string, unknown>)?.detail
  return typeof detail === 'string' ? detail : null
}

// --- reports ---
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

// --- create board (admin only) ---
const newBoard = reactive({ slug: '', title: '', description: '', bump_limit: '300' })
const isCreating = ref(false)
const createError = ref<string | null>(null)

async function onCreate() {
  createError.value = null
  isCreating.value = true
  try {
    await createBoard({
      slug: newBoard.slug,
      title: newBoard.title,
      description: newBoard.description || null,
      bump_limit: Number(newBoard.bump_limit) || 300,
    })
    await queryClient.invalidateQueries({ queryKey: boardsQueryKey })
    newBoard.slug = ''
    newBoard.title = ''
    newBoard.description = ''
    newBoard.bump_limit = '300'
  } catch (error: unknown) {
    createError.value = errorDetail(error) ?? 'Failed to create board.'
  } finally {
    isCreating.value = false
  }
}

// --- edit board (admin only) ---
const editingSlug = ref<string | null>(null)
const editForm = reactive({ title: '', description: '', bump_limit: '300', is_active: true })
const isSaving = ref(false)
const editError = ref<string | null>(null)

function startEdit(board: BoardResponse) {
  editingSlug.value = board.slug
  editForm.title = board.title
  editForm.description = board.description ?? ''
  editForm.bump_limit = String(board.bump_limit)
  editForm.is_active = board.is_active
  editError.value = null
}

function cancelEdit() {
  editingSlug.value = null
}

async function onSave(slug: string) {
  editError.value = null
  isSaving.value = true
  try {
    await updateBoard(slug, {
      title: editForm.title,
      description: editForm.description || null,
      bump_limit: Number(editForm.bump_limit) || 300,
      is_active: editForm.is_active,
    })
    await queryClient.invalidateQueries({ queryKey: boardsQueryKey })
    editingSlug.value = null
  } catch (error: unknown) {
    editError.value = errorDetail(error) ?? 'Failed to save board.'
  } finally {
    isSaving.value = false
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

    <!-- board management — admin only (create + edit are admin-restricted) -->
    <section v-if="auth.isAdmin" class="mt-10">
      <h2 class="text-lg font-medium mb-3">Boards</h2>

      <form
        class="flex flex-wrap items-end gap-2 mb-4 border border-border rounded p-3"
        @submit.prevent="onCreate"
      >
        <div class="flex flex-col gap-1">
          <label for="board-slug" class="text-xs font-medium">Slug</label>
          <BaseInput id="board-slug" v-model="newBoard.slug" placeholder="b" />
        </div>
        <div class="flex flex-col gap-1">
          <label for="board-title" class="text-xs font-medium">Title</label>
          <BaseInput id="board-title" v-model="newBoard.title" placeholder="Random" />
        </div>
        <div class="flex flex-col gap-1 flex-1 min-w-40">
          <label for="board-description" class="text-xs font-medium">Description</label>
          <BaseInput id="board-description" v-model="newBoard.description" placeholder="(optional)" />
        </div>
        <div class="flex flex-col gap-1 w-24">
          <label for="board-bump" class="text-xs font-medium">Bump limit</label>
          <BaseInput id="board-bump" v-model="newBoard.bump_limit" type="number" />
        </div>
        <BaseButton type="submit" variant="primary" size="sm" :disabled="isCreating">
          {{ isCreating ? 'Creating…' : 'Create board' }}
        </BaseButton>
        <p v-if="createError" class="w-full text-sm text-red-500">{{ createError }}</p>
      </form>

      <ul class="flex flex-col gap-2">
        <li
          v-for="board in boards ?? []"
          :key="board.slug"
          class="border border-border rounded p-3 text-sm"
        >
          <div v-if="editingSlug === board.slug" class="flex flex-col gap-2">
            <div class="flex flex-wrap items-end gap-2">
              <span class="font-mono text-secondary self-center">/{{ board.slug }}/</span>
              <div class="flex flex-col gap-1 flex-1 min-w-32">
                <label for="edit-title" class="text-xs font-medium">Title</label>
                <BaseInput id="edit-title" v-model="editForm.title" />
              </div>
              <div class="flex flex-col gap-1 flex-1 min-w-40">
                <label for="edit-description" class="text-xs font-medium">Description</label>
                <BaseInput id="edit-description" v-model="editForm.description" />
              </div>
              <div class="flex flex-col gap-1 w-24">
                <label for="edit-bump" class="text-xs font-medium">Bump limit</label>
                <BaseInput id="edit-bump" v-model="editForm.bump_limit" type="number" />
              </div>
              <label class="flex items-center gap-1 self-center text-xs">
                <input v-model="editForm.is_active" type="checkbox" /> active
              </label>
            </div>
            <div class="flex gap-2">
              <BaseButton variant="primary" size="sm" :disabled="isSaving" @click="onSave(board.slug)">
                {{ isSaving ? 'Saving…' : 'Save' }}
              </BaseButton>
              <BaseButton variant="ghost" size="sm" @click="cancelEdit">Cancel</BaseButton>
            </div>
            <p v-if="editError" class="text-sm text-red-500">{{ editError }}</p>
          </div>
          <div v-else class="flex items-center gap-3">
            <span class="font-mono text-secondary">/{{ board.slug }}/</span>
            <span class="flex-1">{{ board.title }}</span>
            <span v-if="!board.is_active" class="text-secondary italic">disabled</span>
            <BaseButton variant="ghost" size="sm" @click="startEdit(board)">Edit</BaseButton>
          </div>
        </li>
      </ul>
    </section>
  </div>
</template>
