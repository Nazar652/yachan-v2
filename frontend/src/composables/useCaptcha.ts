import { useQuery } from '@tanstack/vue-query'
import { fetchCaptcha } from '@/api/captcha'

export const CAPTCHA_QUERY_KEY = ['captcha'] as const

export function useCaptcha() {
  return useQuery({
    queryKey: CAPTCHA_QUERY_KEY,
    queryFn: fetchCaptcha,
    // captcha images are single-use, so never serve a stale one
    staleTime: 0,
    gcTime: 0,
  })
}

