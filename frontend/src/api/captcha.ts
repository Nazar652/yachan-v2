import { apiClient } from '@/api/client'
import type { CaptchaChallengeResponse } from '@/api/types'

export async function fetchCaptcha(): Promise<CaptchaChallengeResponse> {
  const { data, error } = await apiClient.GET('/api/captcha')
  if (error) throw error
  return data
}

