import { apiClient } from '@/api/client'
import type { BanCreate, BanResponse, ReportResponse, TokenResponse } from '@/api/types'

export async function modLogin(username: string, password: string): Promise<TokenResponse> {
  const { data, error } = await apiClient.POST('/api/mod/login', {
    body: { username, password },
  })
  if (error) throw error
  return data
}

export async function listReports(): Promise<ReportResponse[]> {
  const { data, error } = await apiClient.GET('/api/mod/reports')
  if (error) throw error
  return data
}

export async function resolveReport(reportId: number): Promise<void> {
  const { error } = await apiClient.POST('/api/mod/reports/{report_id}/resolve', {
    params: { path: { report_id: reportId } },
  })
  if (error) throw error
}

export async function deletePost(boardSlug: string, postNumber: number): Promise<void> {
  const { error } = await apiClient.DELETE('/api/mod/{board_slug}/posts/{post_number}', {
    params: { path: { board_slug: boardSlug, post_number: postNumber } },
  })
  if (error) throw error
}

export async function setThreadLocked(
  boardSlug: string,
  threadId: number,
  locked: boolean,
): Promise<void> {
  const { error } = await apiClient.POST('/api/mod/{board_slug}/threads/{thread_id}/lock', {
    params: { path: { board_slug: boardSlug, thread_id: threadId }, query: { locked } },
  })
  if (error) throw error
}

export async function setThreadSticky(
  boardSlug: string,
  threadId: number,
  sticky: boolean,
): Promise<void> {
  const { error } = await apiClient.POST('/api/mod/{board_slug}/threads/{thread_id}/sticky', {
    params: { path: { board_slug: boardSlug, thread_id: threadId }, query: { sticky } },
  })
  if (error) throw error
}

export async function banPoster(
  boardSlug: string,
  postNumber: number,
  data: BanCreate,
): Promise<BanResponse> {
  const { data: ban, error } = await apiClient.POST('/api/mod/{board_slug}/posts/{post_number}/ban', {
    params: { path: { board_slug: boardSlug, post_number: postNumber } },
    body: data,
  })
  if (error) throw error
  return ban
}
