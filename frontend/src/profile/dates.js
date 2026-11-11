// Stored dates are YYYY-MM-DD strings (or null). A month picker produces YYYY-MM, which is stored
// as the first day of that month.

const ISO_DATE = /^(\d{4})-(\d{2})-(\d{2})$/

// True only for a real calendar date written as YYYY-MM-DD.
export function isIsoDate(value) {
    if (typeof value !== 'string') return false
    const m = ISO_DATE.exec(value)
    if (!m) return false
    const [y, mo, d] = [Number(m[1]), Number(m[2]), Number(m[3])]
    const date = new Date(Date.UTC(y, mo - 1, d))
    return date.getUTCFullYear() === y && date.getUTCMonth() === mo - 1 && date.getUTCDate() === d
}

// '2026-06-01' -> '2026-06' (value for <input type="month">). Anything else -> ''.
export function isoToMonth(iso) {
    return isIsoDate(iso) ? iso.slice(0, 7) : ''
}

// '2026-06' -> '2026-06-01'. Empty or malformed -> null.
export function monthToIso(month) {
    return typeof month === 'string' && /^\d{4}-(0[1-9]|1[0-2])$/.test(month) ? `${month}-01` : null
}

const parts = (iso, options) => new Date(`${iso}T00:00:00Z`).toLocaleDateString('en-US', { ...options, timeZone: 'UTC' })

// '2026-06-01' -> 'Jun 2026'
export function formatMonth(iso) {
    return isIsoDate(iso) ? parts(iso, { month: 'short', year: 'numeric' }) : ''
}

// '2026-06-12' -> 'Jun 12, 2026'
export function formatDay(iso) {
    return isIsoDate(iso) ? parts(iso, { month: 'short', day: 'numeric', year: 'numeric' }) : ''
}

// ('2026-06-01', null) -> 'Jun 2026 – Present'. A record with no dates at all shows nothing.
export function formatRange(start, end) {
    const from = formatMonth(start)
    const to = formatMonth(end)
    if (!from && !to) return ''
    if (!from) return to
    return `${from} – ${to || 'Present'}`
}
