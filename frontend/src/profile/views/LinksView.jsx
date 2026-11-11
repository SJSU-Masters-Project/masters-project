import React from 'react'
import { ExternalLink } from 'lucide-react'
import { safeUrl } from '../safeHtml'
import styles from './sections.module.css'

/** @param {{ items: import('../schema').LinkItem[] }} props */
export default function LinksView({ items }) {
    return (
        <div className={styles.linkGrid}>
            {items.map((item, i) => {
                const url = safeUrl(item.url)
                const body = (
                    <>
                        <span className={styles.linkName}>
                            {item.name} {url && <ExternalLink size={14} aria-hidden="true" />}
                        </span>
                        <span className={styles.linkUrl}>{item.url}</span>
                        {item.description && <span className={styles.text}>{item.description}</span>}
                    </>
                )
                return url ? (
                    <a key={item._key || i} href={url} target="_blank" rel="noopener noreferrer" className={styles.linkCard}>
                        {body}
                    </a>
                ) : (
                    <div key={item._key || i} className={styles.linkCard}>
                        {body}
                    </div>
                )
            })}
        </div>
    )
}
