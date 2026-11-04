const KEY = 'careers.session'

export function loadSession() {
    try {
        return JSON.parse(sessionStorage.getItem(KEY)) || null
    } catch {
        return null
    }
}

export function saveSession(session) {
    try {
        sessionStorage.setItem(KEY, JSON.stringify(session))
    } catch {
        // storage can be blocked (private windows); the session then lasts for this page only
    }
}

export function clearSession() {
    try {
        sessionStorage.removeItem(KEY)
    } catch {
        // nothing to clear
    }
}

// Development sign-in: the API accepts `Bearer dev:<email>:<role>` while CAREERS_DEV_AUTH is on.
export const devToken = (email, role) => `dev:${email.trim().toLowerCase()}:${role}`

export class LoginError extends Error {
    constructor(message, kind) {
        super(message)
        this.kind = kind // 'invalid' (do not retry as-is) or 'network' (retry)
    }
}

// Verifies a token against GET /api/v1/me and returns the user ({ id, email, role, created_at }).
export async function fetchMe(token) {
    let res
    try {
        res = await fetch('/api/v1/me', { headers: { Authorization: `Bearer ${token}` } })
    } catch {
        throw new LoginError('Unable to reach the server. Please try again.', 'network')
    }
    if (res.ok) return res.json()
    let message = res.status >= 500 ? 'The server is unavailable. Please try again.' : 'Sign-in failed.'
    try {
        message = (await res.json())?.error?.message || message
    } catch {
        // non-JSON error body
    }
    throw new LoginError(message, res.status >= 500 ? 'network' : 'invalid')
}
