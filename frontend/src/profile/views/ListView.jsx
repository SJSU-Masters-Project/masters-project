import React from 'react'
import { formatDay } from '../dates'
import { TextLink } from './ExternalLink'
import styles from './sections.module.css'

/** @param {{ items: import('../schema').ListItem[] }} props */
export default function ListView({ items }) {
    return (
        <ul className={styles.rows}>
            {items.map((item, i) => {
                const meta = [item.subtitle, formatDay(item.date)].filter(Boolean).join(' · ')
                return (
                    <li key={item._key || i} className={styles.row}>
                        <div className={styles.rowMain}>
                            <h3 className={styles.itemTitle}>{item.title}</h3>
                            {meta && <p className={styles.entryMeta}>{meta}</p>}
                            {item.description && <p className={styles.entryText}>{item.description}</p>}
                        </div>
                        {item.link && (
                            <TextLink href={item.link}>
                                Verify<span className={styles.sr}> {item.title}</span>
                            </TextLink>
                        )}
                    </li>
                )
            })}
        </ul>
    )
}
