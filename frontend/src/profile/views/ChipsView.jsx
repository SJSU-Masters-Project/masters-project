import React from 'react'
import styles from './sections.module.css'

function Dots({ value }) {
    return (
        <span className={styles.dots} aria-hidden="true">
            {[1, 2, 3, 4, 5].map((n) => (
                <span key={n} className={`${styles.dot} ${n <= value ? styles.dotOn : ''}`} />
            ))}
        </span>
    )
}

/** @param {{ items: import('../schema').ChipsItem[] }} props */
export default function ChipsView({ items }) {
    return (
        <div className={styles.groups}>
            {items.map((group, i) => (
                <section key={group._key || i} className={styles.group}>
                    <h3 className={styles.groupTitle}>{group.category}</h3>
                    <ul className={styles.skills}>
                        {group.skillsList.map((s, j) => (
                            <li key={s._key || j} className={styles.skill}>
                                <span>{s.skillName}</span>
                                <Dots value={s.proficiency} />
                                <span className={styles.sr}>{s.proficiency} of 5</span>
                            </li>
                        ))}
                    </ul>
                </section>
            ))}
        </div>
    )
}
