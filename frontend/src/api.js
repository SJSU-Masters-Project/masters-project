import { clearSession, loadSession } from './auth'

export const SESSION_EXPIRED = 'careers:session-expired'

export class ApiError extends Error {
    constructor(message, status, code, details) {
        super(message)
        this.status = status
        this.code = code
        this.details = details || {}
    }
}

const query = (params) => {
    const qs = new URLSearchParams()
    Object.entries(params || {}).forEach(([k, v]) => {
        if (v !== undefined && v !== null && v !== '') qs.set(k, v)
    })
    const s = qs.toString()
    return s ? `?${s}` : ''
}

async function request(path, { method = 'GET', body, form, params } = {}) {
    const session = loadSession()
    const headers = {}
    if (session?.token) headers.Authorization = `Bearer ${session.token}`
    let payload
    if (form) {
        payload = form
    } else if (body !== undefined) {
        headers['Content-Type'] = 'application/json'
        payload = JSON.stringify(body)
    }

    let res
    try {
        res = await fetch(`/api/v1${path}${query(params)}`, { method, headers, body: payload })
    } catch {
        throw new ApiError('Unable to reach the server. Please try again.', 0, 'network')
    }

    if (res.ok) return res

    let err = { message: res.status >= 500 ? 'The server is unavailable. Please try again.' : 'Request failed.' }
    try {
        err = (await res.json())?.error || err
    } catch {
        // non-JSON error body
    }
    if (res.status === 401 && session) {
        clearSession()
        window.dispatchEvent(new Event(SESSION_EXPIRED))
    }
    throw new ApiError(err.message, res.status, err.code, err.details)
}

export async function api(path, options) {
    const res = await request(path, options)
    return res.status === 204 ? null : res.json()
}

// Downloads a file through the authenticated API and hands it to the browser.
export async function downloadFile(path, filename) {
    const res = await request(path)
    const url = URL.createObjectURL(await res.blob())
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(url)
}

// True when the failure is one the user can fix by trying again.
export const isRetryable = (err) => !(err instanceof ApiError) || err.status === 0 || err.status >= 500
