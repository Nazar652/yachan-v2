import { useQueryClient } from '@tanstack/vue-query'

import { reorderBoards } from '@/api/mod'
import { boardsQueryKey } from '@/composables/useBoards'

// pure helper: a new array with the item at `from` spliced out and reinserted at
// `to`. kept separate from the drag wiring so the only logic worth testing is a
// plain, side-effect-free function.
export function moveItem<T>(items: T[], from: number, to: number): T[] {
  const next = items.slice()
  const moved = next.splice(from, 1)
  next.splice(to, 0, ...moved)
  return next
}

export function useBoardReorder() {
  const queryClient = useQueryClient()

  // persist a full new ordering, then refetch so the canonical order comes back
  // from the server (board listings everywhere rely on the boards query)
  async function reorder(slugs: string[]): Promise<void> {
    await reorderBoards(slugs)
    await queryClient.invalidateQueries({ queryKey: boardsQueryKey })
  }

  return { reorder }
}
