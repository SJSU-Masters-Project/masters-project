// Saved job ids, mirrored to localStorage so a shortlist survives a reload. Every read and write is
// wrapped in try/catch because storage can be unavailable (private windows, quota, blocked cookies).

const KEY = 'careers.savedJobs'

export function loadSaved() {
    try {
        const raw = JSON.parse(localStorage.getItem(KEY))
        return Array.isArray(raw) ? raw.map(String) : []
    } catch {
        return []
    }
}

export function storeSaved(ids) {
    try {
        localStorage.setItem(KEY, JSON.stringify([...ids]))
    } catch {
        // not persisted; the shortlist still lives in component state for this session
    }
}
