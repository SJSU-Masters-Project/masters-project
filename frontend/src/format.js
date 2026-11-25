export const WORK_MODES = [
    { value: 'on_site', label: 'On-site' },
    { value: 'hybrid', label: 'Hybrid' },
    { value: 'remote', label: 'Remote' },
]

export const EMPLOYMENT_TYPES = [
    { value: 'full_time', label: 'Full-time' },
    { value: 'part_time', label: 'Part-time' },
    { value: 'internship', label: 'Internship' },
    { value: 'contract', label: 'Contract' },
    { value: 'co_op', label: 'Co-op' },
]

const labelOf = (list, value) => list.find((i) => i.value === value)?.label || value
export const workModeLabel = (v) => labelOf(WORK_MODES, v)
export const employmentLabel = (v) => labelOf(EMPLOYMENT_TYPES, v)

export function formatDate(iso) {
    if (!iso) return ''
    const d = new Date(iso)
    return Number.isNaN(d.getTime()) ? '' : d.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })
}

export function formatBytes(n) {
    if (n < 1024) return `${n} B`
    if (n < 1024 * 1024) return `${(n / 1024).toFixed(0)} KB`
    return `${(n / (1024 * 1024)).toFixed(1)} MB`
}

// "a, b, c" -> ['a','b','c'] with blanks and case-insensitive duplicates removed.
export function splitList(text) {
    const seen = new Set()
    return String(text || '')
        .split(/[,\n]/)
        .map((s) => s.trim())
        .filter((s) => {
            const k = s.toLowerCase()
            if (!s || seen.has(k)) return false
            seen.add(k)
            return true
        })
}

// Flattens the API's { field: [messages] } details into one readable line each.
export function detailLines(details) {
    return Object.entries(details || {}).flatMap(([field, msgs]) =>
        (Array.isArray(msgs) ? msgs : [msgs]).map((m) => `${field.replace(/\//g, ' › ')}: ${typeof m === 'string' ? m : JSON.stringify(m)}`)
    )
}
