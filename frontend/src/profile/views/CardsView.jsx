import React from 'react'
import { IconLink } from './ExternalLink'
import styles from './sections.module.css'

/** @param {{ items: import('../schema').CardItem[] }} props */
export default function CardsView({ items }) {
    return (
        <div className={styles.cards}>
            {items.map((item, i) => (
                <article key={item._key || i} className={styles.item}>
                    <div className={styles.itemHead}>
                        <h3 className={styles.itemTitle}>{item.title}</h3>
                        <IconLink href={item.link} label={`Open ${item.title}`} />
                    </div>
                    {item.purpose && <p className={styles.text}>{item.purpose}</p>}
                    {item.techStack?.length > 0 && (
                        <ul className={styles.tags} aria-label="Tech stack">
                            {item.techStack.map((t) => (
                                <li key={t} className={styles.tag}>
                                    {t}
                                </li>
                            ))}
                        </ul>
                    )}
                    {item.features?.length > 0 && (
                        <ul className={styles.bullets}>
                            {item.features.map((f) => (
                                <li key={f}>{f}</li>
                            ))}
                        </ul>
                    )}
                </article>
            ))}
        </div>
    )
}
