import DOMPurify from 'dompurify'

// Rich text allowlist: p, br, strong, em, ul, ol, li and a[href] with an http(s) href. Nothing else.
const ALLOWED_TAGS = ['p', 'br', 'strong', 'em', 'ul', 'ol', 'li', 'a']
const ALLOWED_ATTR = ['href']
const HTTP_URL = /^https?:\/\//i

const base = { ALLOWED_TAGS, ALLOWED_ATTR, ALLOWED_URI_REGEXP: HTTP_URL, ALLOW_DATA_ATTR: false, ALLOW_ARIA_ATTR: false }

// A second instance adds target/rel to links, only when rendering. Stored HTML keeps just the href.
const renderPurify = DOMPurify(globalThis.window)
renderPurify.addHook('afterSanitizeAttributes', (node) => {
    if (node.tagName === 'A' && node.hasAttribute('href')) {
        node.setAttribute('target', '_blank')
        node.setAttribute('rel', 'noopener noreferrer')
    }
})

// Cleans an HTML string for storage. Run on save in the editor, and again by the backend.
export function sanitize(html) {
    return DOMPurify.sanitize(typeof html === 'string' ? html : '', base)
}

// Cleans an HTML string for display: the same allowlist, and links open in a new tab.
export function sanitizeForRender(html) {
    return renderPurify.sanitize(typeof html === 'string' ? html : '', base)
}

// Returns the trimmed URL when it is a plain http(s) address, otherwise null.
export function safeUrl(url) {
    if (typeof url !== 'string') return null
    const value = url.trim()
    if (!HTTP_URL.test(value) || /\s/.test(value)) return null
    try {
        const parsed = new URL(value)
        return (parsed.protocol === 'http:' || parsed.protocol === 'https:') && parsed.hostname ? value : null
    } catch {
        return null
    }
}
