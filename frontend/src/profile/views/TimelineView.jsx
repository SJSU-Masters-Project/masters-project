import React from 'react'
import { formatRange } from '../dates'
import { TextLink } from './ExternalLink'
import styles from './sections.module.css'

// Renders the timeline template. With `education`, items use degree / institute / grade instead of
// title / subtitle / description.
export default function TimelineView({ items, education = false }) {
    return (
        <ol className={styles.timeline}>
            {items.map((item, i) => {
                const title = education ? item.degree : item.title
                const subtitle = education ? item.institute : item.subtitle
                const detail = education ? item.grade : item.description
                const range = formatRange(item.startDate, item.endDate)
                return (
                    <li key={item._key || i} className={styles.entry}>
                        <h3 className={styles.entryTitle}>{title}</h3>
                        <p className={styles.entrySub}>
                            <TextLink href={item.link}>{subtitle}</TextLink>
                        </p>
                        {range && <p className={styles.entryMeta}>{range}</p>}
                        {detail && <p className={styles.entryText}>{education ? `Grade: ${detail}` : detail}</p>}
                    </li>
                )
            })}
        </ol>
    )
}
