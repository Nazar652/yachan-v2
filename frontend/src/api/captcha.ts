import { apiClient } from '@/api/client'
import { toApiError } from '@/api/errors'
import type { CaptchaChallengeResponse } from '@/api/types'

export async function fetchCaptcha(): Promise<CaptchaChallengeResponse> {
  const { data, error, response } = await apiClient.GET('/api/captcha')
  if (error) throw toApiError(error, response)
  return data
}

