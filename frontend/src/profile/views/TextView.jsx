import React, { useMemo } from 'react'
import { sanitizeForRender } from '../safeHtml'
import styles from './sections.module.css'

// Rich text. The HTML is sanitized again here, so stored content is never trusted on render.
export default function TextView({ items }) {
    const html = useMemo(() => sanitizeForRender(items[0] || ''), [items])
    if (!html) return null
    return <div className={styles.rich} dangerouslySetInnerHTML={{ __html: html }} />
}
