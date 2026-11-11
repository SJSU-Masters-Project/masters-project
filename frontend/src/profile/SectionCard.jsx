import React from 'react'
import { ArrowDown, ArrowUp, Eye, EyeOff, Pencil, Trash2 } from 'lucide-react'
import { Pill } from '../ui'
import { EDUCATION, TEMPLATES } from './templates'
import SectionView from './views/SectionView'
import styles from './views/sections.module.css'

// One section on the profile page: heading, "Hidden" pill, actions and the read-only view.
// Education passes `education` and has no move or delete buttons (it is always first).
export default function SectionCard({ section, education = false, busy, isFirst, isLast, onEdit, onToggleVisible, onMove, onDelete }) {
    const def = education ? EDUCATION : TEMPLATES[section.template]
    const heading = section.heading
    const empty = !section.data?.length
    return (
        <section className={`${styles.sectionCard} ${section.visible ? '' : styles.hiddenSection}`} aria-label={heading}>
            <div className={styles.sectionHead}>
                <div className={styles.sectionHeading}>
                    <h2 className={styles.sectionTitle}>{heading}</h2>
                    <Pill tone="muted">{education ? 'Timeline' : def.label}</Pill>
                    {!section.visible && <Pill tone="warning">Hidden</Pill>}
                </div>
                <div className={styles.sectionActions}>
                    <button type="button" className="btn outlined small" onClick={onEdit} disabled={busy}>
                        <Pencil size={14} aria-hidden="true" /> Edit<span className={styles.sr}> {heading}</span>
                    </button>
                    <button type="button" className="btn outlined small" onClick={onToggleVisible} disabled={busy}>
                        {section.visible ? <EyeOff size={14} aria-hidden="true" /> : <Eye size={14} aria-hidden="true" />}
                        {section.visible ? 'Hide' : 'Show'}
                        <span className={styles.sr}> {heading}</span>
                    </button>
                    {!education && (
                        <>
                            <button
                                type="button"
                                className={styles.iconBtn}
                                onClick={() => onMove(-1)}
                                disabled={busy || isFirst}
                                aria-label={`Move ${heading} up`}
                            >
                                <ArrowUp size={16} aria-hidden="true" />
                            </button>
                            <button
                                type="button"
                                className={styles.iconBtn}
                                onClick={() => onMove(1)}
                                disabled={busy || isLast}
                                aria-label={`Move ${heading} down`}
                            >
                                <ArrowDown size={16} aria-hidden="true" />
                            </button>
                            <button
                                type="button"
                                className={`${styles.iconBtn} ${styles.iconBtnDanger}`}
                                onClick={onDelete}
                                disabled={busy}
                                aria-label={`Delete ${heading}`}
                            >
                                <Trash2 size={16} aria-hidden="true" />
                            </button>
                        </>
                    )}
                </div>
            </div>
            {empty ? (
                <p className={styles.sectionEmpty}>Nothing here yet. Choose Edit to add {education ? 'your education' : 'items'}.</p>
            ) : (
                <SectionView section={section} education={education} />
            )}
        </section>
    )
}
