import type { MaybeRefOrGetter } from 'vue'
import { toValue } from 'vue'
import { useQuery } from '@tanstack/vue-query'
import { fetchCaptcha } from '@/api/captcha'

export const CAPTCHA_QUERY_KEY = ['captcha'] as const

// admins post without solving a captcha, so callers can pass enabled=false to
// skip fetching a challenge that will never be shown
export function useCaptcha(enabled: MaybeRefOrGetter<boolean> = true) {
  return useQuery({
    queryKey: CAPTCHA_QUERY_KEY,
    queryFn: fetchCaptcha,
    enabled: () => toValue(enabled),
    // captcha images are single-use, so never serve a stale one
    staleTime: 0,
    gcTime: 0,
  })
}

