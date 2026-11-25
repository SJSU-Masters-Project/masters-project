import { afterEach, expect, it, vi } from 'vitest'
import { api, setTokenProvider } from './api'

afterEach(() => {
    vi.unstubAllGlobals()
    setTokenProvider(async () => null)
})

it('gets a fresh session token for each request and preserves API errors', async () => {
    let sequence = 0
    setTokenProvider(async () => `token-${++sequence}`)
    const fetchMock = vi
        .fn()
        .mockResolvedValueOnce({ ok: true, status: 200, json: async () => ({ id: '1' }) })
        .mockResolvedValueOnce({
            ok: false,
            status: 403,
            json: async () => ({ error: { code: 'role_required', message: 'Choose a role' } }),
        })
    vi.stubGlobal('fetch', fetchMock)
    await expect(api('/me')).resolves.toEqual({ id: '1' })
    await expect(api('/me/role', { method: 'POST', body: { role: 'candidate' } })).rejects.toMatchObject({
        status: 403,
        code: 'role_required',
    })
    expect(fetchMock.mock.calls[0][1].headers.Authorization).toBe('Bearer token-1')
    expect(fetchMock.mock.calls[1][1].headers.Authorization).toBe('Bearer token-2')
    expect(fetchMock.mock.calls[1][1].body).toBe('{"role":"candidate"}')
})
