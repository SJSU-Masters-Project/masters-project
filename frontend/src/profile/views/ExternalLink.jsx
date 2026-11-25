import React from 'react'
import { ExternalLink as ExternalLinkIcon } from 'lucide-react'
import { safeUrl } from '../safeHtml'
import styles from './sections.module.css'

// Icon-only link to an external page. Renders nothing unless the address is a plain http(s) URL.
export function IconLink({ href, label }) {
    const url = safeUrl(href)
    if (!url) return null
    return (
        <a href={url} target="_blank" rel="noopener noreferrer" className={styles.extLink} aria-label={label}>
            <ExternalLinkIcon size={16} aria-hidden="true" />
        </a>
    )
}

// Text link to an external page; falls back to plain text when the address is not a safe URL.
export function TextLink({ href, children }) {
    const url = safeUrl(href)
    if (!url) return <>{children}</>
    return (
        <a href={url} target="_blank" rel="noopener noreferrer" className={styles.textLink}>
            {children}
        </a>
    )
}
