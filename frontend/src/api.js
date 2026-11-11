import { useAuth } from '@clerk/react'
import { useCallback } from 'react'

export class ApiError extends Error {
    constructor(message, status) {
        super(message)
        this.status = status // 0 when the server could not be reached
    }
}

// Calls the careers API under /api: the same origin in production (nginx proxies it), and
// Vite's dev-server proxy locally. Clerk session tokens are short-lived, so a token is fetched
// for every request; Clerk caches it and refreshes it when it is about to expire.
export function useApi() {
    const { getToken } = useAuth()
    return useCallback(
        async (path, options = {}) => {
            const token = await getToken()
            const headers = { ...options.headers }
            if (token) headers.Authorization = `Bearer ${token}`
            if (typeof options.body === 'string') headers['Content-Type'] = 'application/json'

            let res
            try {
                res = await fetch(`/api${path}`, { ...options, headers })
            } catch {
                throw new ApiError('Unable to reach the server. Please try again.', 0)
            }
            const body = await res.json().catch(() => null)
            if (!res.ok) {
                throw new ApiError(body?.error?.message || `Request failed (${res.status}).`, res.status)
            }
            return body
        },
        [getToken]
    )
}
