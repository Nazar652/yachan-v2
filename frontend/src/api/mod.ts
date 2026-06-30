import { apiClient } from '@/api/client'
import { toApiError } from '@/api/errors'
import type {
  BanCreate,
  BanResponse,
  BoardCreate,
  BoardResponse,
  BoardUpdate,
  ReportResponse,
  TokenResponse,
} from '@/api/types'

export async function modLogin(username: string, password: string): Promise<TokenResponse> {
  const { data, error, response } = await apiClient.POST('/api/mod/login', {
    body: { username, password },
  })
  if (error) throw toApiError(error, response)
  return data
}

export async function createBoard(data: BoardCreate): Promise<BoardResponse> {
  const { data: board, error, response } = await apiClient.POST('/api/mod/boards', { body: data })
  if (error) throw toApiError(error, response)
  return board
}

export async function updateBoard(slug: string, data: BoardUpdate): Promise<BoardResponse> {
  const { data: board, error, response } = await apiClient.PATCH('/api/mod/boards/{board_slug}', {
    params: { path: { board_slug: slug } },
    body: data,
  })
  if (error) throw toApiError(error, response)
  return board
}

export async function reorderBoards(slugs: string[]): Promise<BoardResponse[]> {
  const { data, error, response } = await apiClient.PUT('/api/mod/boards/order', { body: { slugs } })
  if (error) throw toApiError(error, response)
  return data
}

export async function listReports(): Promise<ReportResponse[]> {
  const { data, error, response } = await apiClient.GET('/api/mod/reports')
  if (error) throw toApiError(error, response)
  return data
}

export async function resolveReport(reportId: number): Promise<void> {
  const { error, response } = await apiClient.POST('/api/mod/reports/{report_id}/resolve', {
    params: { path: { report_id: reportId } },
  })
  if (error) throw toApiError(error, response)
}

export async function deletePost(boardSlug: string, postNumber: number): Promise<void> {
  const { error, response } = await apiClient.DELETE('/api/mod/{board_slug}/posts/{post_number}', {
    params: { path: { board_slug: boardSlug, post_number: postNumber } },
  })
  if (error) throw toApiError(error, response)
}

export async function setThreadLocked(
  boardSlug: string,
  threadId: number,
  locked: boolean,
): Promise<void> {
  const { error, response } = await apiClient.POST('/api/mod/{board_slug}/threads/{thread_id}/lock', {
    params: { path: { board_slug: boardSlug, thread_id: threadId }, query: { locked } },
  })
  if (error) throw toApiError(error, response)
}

export async function setThreadSticky(
  boardSlug: string,
  threadId: number,
  sticky: boolean,
): Promise<void> {
  const { error, response } = await apiClient.POST('/api/mod/{board_slug}/threads/{thread_id}/sticky', {
    params: { path: { board_slug: boardSlug, thread_id: threadId }, query: { sticky } },
  })
  if (error) throw toApiError(error, response)
}

export async function banPoster(
  boardSlug: string,
  postNumber: number,
  data: BanCreate,
): Promise<BanResponse> {
  const { data: ban, error, response } = await apiClient.POST('/api/mod/{board_slug}/posts/{post_number}/ban', {
    params: { path: { board_slug: boardSlug, post_number: postNumber } },
    body: data,
  })
  if (error) throw toApiError(error, response)
  return ban
}
