<script setup lang="ts">
import { reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useQueryClient } from '@tanstack/vue-query'

import { useAuthStore } from '@/stores/auth'
import { useReports, reportsQueryKey } from '@/composables/useReports'
import { useBoards, boardsQueryKey } from '@/composables/useBoards'
import { useBoardReorder, moveItem } from '@/composables/useBoardReorder'
import { resolveReport, createBoard, updateBoard } from '@/api/mod'
import type { BoardResponse } from '@/api/types'
import BaseButton from '@/components/ui/BaseButton.vue'
import BaseInput from '@/components/ui/BaseInput.vue'
import MonogramSeal from '@/components/brand/MonogramSeal.vue'

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
const newBoard = reactive({ slug: '', title: '', description: '', bump_limit: '300', is_nsfw: false })
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
      is_nsfw: newBoard.is_nsfw,
    })
    await queryClient.invalidateQueries({ queryKey: boardsQueryKey })
    newBoard.slug = ''
    newBoard.title = ''
    newBoard.description = ''
    newBoard.bump_limit = '300'
    newBoard.is_nsfw = false
  } catch (error: unknown) {
    createError.value = errorDetail(error) ?? 'Failed to create board.'
  } finally {
    isCreating.value = false
  }
}

// --- edit board (admin only) ---
const editingSlug = ref<string | null>(null)
const editForm = reactive({ title: '', description: '', bump_limit: '300', is_active: true, is_nsfw: false })
const isSaving = ref(false)
const editError = ref<string | null>(null)

function startEdit(board: BoardResponse) {
  editingSlug.value = board.slug
  editForm.title = board.title
  editForm.description = board.description ?? ''
  editForm.bump_limit = String(board.bump_limit)
  editForm.is_active = board.is_active
  editForm.is_nsfw = board.is_nsfw
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
      is_nsfw: editForm.is_nsfw,
    })
    await queryClient.invalidateQueries({ queryKey: boardsQueryKey })
    editingSlug.value = null
  } catch (error: unknown) {
    editError.value = errorDetail(error) ?? 'Failed to save board.'
  } finally {
    isSaving.value = false
  }
}

// --- reorder boards (admin only, native drag and drop) ---
const { reorder } = useBoardReorder()
// a local, reorderable copy of the server list; reset whenever the query refetches
const orderedBoards = ref<BoardResponse[]>([])
watch(
  boards,
  (value) => {
    orderedBoards.value = value ? [...value] : []
  },
  { immediate: true },
)

const dragIndex = ref<number | null>(null)
const overIndex = ref<number | null>(null)
const reorderError = ref<string | null>(null)

function onDragStart(index: number) {
  dragIndex.value = index
}

function onDragOver(index: number) {
  overIndex.value = index
}

function onDragEnd() {
  dragIndex.value = null
  overIndex.value = null
}

async function onDrop(index: number) {
  const from = dragIndex.value
  onDragEnd()
  if (from === null || from === index) return
  // optimistic local reorder; the server order comes back on the next refetch
  const next = moveItem(orderedBoards.value, from, index)
  orderedBoards.value = next
  reorderError.value = null
  try {
    await reorder(next.map((item) => item.slug))
  } catch (error: unknown) {
    reorderError.value = errorDetail(error) ?? 'Failed to reorder boards.'
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
  <div class="mx-auto max-w-3xl py-5">
    <div class="mb-5 flex items-center gap-3">
      <MonogramSeal :size="30" />
      <h1 class="text-3xl font-extrabold tracking-tight">Mod dashboard</h1>
      <BaseButton variant="link" size="sm" class="ml-auto" @click="onLogout">Log out</BaseButton>
    </div>

    <div class="mb-3 flex items-center gap-3">
      <h2 class="text-lg font-extrabold">Reports</h2>
      <span class="h-px flex-1 bg-border" />
    </div>

    <p v-if="isPending" class="text-text-muted">Loading…</p>
    <p v-else-if="isError" class="text-danger">Failed to load reports.</p>
    <p
      v-else-if="!reports?.length"
      class="flex items-center gap-3 rounded-card border border-border bg-surface p-4 text-[14.5px] text-text-muted shadow-card"
    >
      <span class="text-greentext" aria-hidden="true">✓</span>
      No open reports. The fields are calm.
    </p>

    <ul v-else class="flex flex-col gap-2">
      <li
        v-for="report in reports"
        :key="report.id"
        class="flex items-center gap-3 rounded-card border border-border bg-surface p-3 text-sm shadow-card"
      >
        <span class="font-mono text-text-muted">#{{ report.id }}</span>
        <span class="font-mono">post {{ report.post_id }}</span>
        <span
          v-if="report.is_auto"
          class="rounded-full bg-gold/25 px-2 py-0.5 font-mono text-[10.5px] font-semibold uppercase tracking-wide text-accent"
          title="auto-flagged by text moderation"
        >
          🤖 auto
        </span>
        <span class="flex-1 truncate">{{ report.reason ?? '(no reason)' }}</span>
        <span class="text-text-muted">{{ formatDate(report.created_at) }}</span>
        <span v-if="report.is_resolved" class="italic text-text-muted">resolved</span>
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
      <div class="mb-3 flex items-center gap-3">
        <h2 class="text-lg font-extrabold">Boards</h2>
        <span class="h-px flex-1 bg-border" />
      </div>

      <form
        class="mb-4 flex flex-wrap items-end gap-2 rounded-card border border-border bg-surface p-4 shadow-card"
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
        <label class="flex items-center gap-1 self-center text-xs">
          <input v-model="newBoard.is_nsfw" type="checkbox" /> 18+
        </label>
        <BaseButton type="submit" variant="primary" size="sm" :disabled="isCreating">
          {{ isCreating ? 'Creating…' : '+ Create' }}
        </BaseButton>
        <p v-if="createError" class="w-full text-sm text-danger">{{ createError }}</p>
      </form>

      <ul class="flex flex-col gap-2">
        <li
          v-for="(board, index) in orderedBoards"
          :key="board.slug"
          class="rounded-card border border-border bg-surface p-3.5 text-sm shadow-card transition-colors hover:border-gold"
          :class="{
            'opacity-50': dragIndex === index,
            'border-gold': overIndex === index && dragIndex !== null && dragIndex !== index,
          }"
          :draggable="editingSlug !== board.slug"
          @dragstart="onDragStart(index)"
          @dragover.prevent="onDragOver(index)"
          @drop="onDrop(index)"
          @dragend="onDragEnd"
        >
          <div v-if="editingSlug === board.slug" class="flex flex-col gap-2">
            <div class="flex flex-wrap items-end gap-2">
              <span class="self-center font-mono font-bold text-gold-2">/{{ board.slug }}/</span>
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
              <label class="flex items-center gap-1 self-center text-xs">
                <input v-model="editForm.is_nsfw" type="checkbox" /> 18+
              </label>
            </div>
            <div class="flex gap-2">
              <BaseButton variant="primary" size="sm" :disabled="isSaving" @click="onSave(board.slug)">
                {{ isSaving ? 'Saving…' : 'Save' }}
              </BaseButton>
              <BaseButton variant="ghost" size="sm" @click="cancelEdit">Cancel</BaseButton>
            </div>
            <p v-if="editError" class="text-sm text-danger">{{ editError }}</p>
          </div>
          <div v-else class="flex items-center gap-3.5">
            <span class="cursor-move select-none text-lg text-text-muted" title="Drag to reorder" aria-hidden="true">⠿</span>
            <span class="min-w-11 font-mono font-bold text-gold-2">/{{ board.slug }}/</span>
            <div class="min-w-0 flex-1">
              <div class="font-display font-bold">{{ board.title }}</div>
              <div v-if="board.description" class="truncate text-xs text-text-muted">{{ board.description }}</div>
            </div>
            <span v-if="board.is_nsfw" class="rounded bg-danger/10 px-1.5 py-0.5 font-mono text-[10px] font-bold text-danger">18+</span>
            <span v-if="!board.is_active" class="italic text-text-muted">disabled</span>
            <BaseButton variant="ghost" size="sm" @click="startEdit(board)">Edit</BaseButton>
          </div>
        </li>
      </ul>
      <p v-if="reorderError" class="mt-2 text-sm text-danger">{{ reorderError }}</p>
    </section>
  </div>
</template>
