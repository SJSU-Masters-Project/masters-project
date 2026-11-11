import React, { Suspense, lazy, useEffect, useId, useMemo, useState } from 'react'
import { Loader2, Save } from 'lucide-react'
import { Field, FormError } from '../../ui'
import ui from '../../ui.module.css'
import { stripKeys } from '../adapters'
import { EDUCATION, TEMPLATES, validateSection } from '../templates'
import CardsEditor from './CardsEditor'
import ChipsEditor from './ChipsEditor'
import EducationEditor from './EducationEditor'
import LinksEditor from './LinksEditor'
import ListEditor from './ListEditor'
import TimelineEditor from './TimelineEditor'
import styles from './editors.module.css'

// The rich text editor (Tiptap) is large, so it loads only when a rich text section is edited.
const TextEditor = lazy(() => import('./TextEditor'))

const EDITORS = { cards: CardsEditor, timeline: TimelineEditor, list: ListEditor, chips: ChipsEditor, links: LinksEditor, text: TextEditor }

// Items whose end date is "not chosen yet" (the box is unticked and the month is empty).
const pendingEndDates = (section) => (section.data || []).filter((item) => item && item.endDate === '').length

// Edits one section: its heading, whether it is shown, and its items. The template is fixed once created.
//   onSave(draft) -> Promise; resolves when saved. `error` is { message, lines } from a failed save.
export default function SectionEditor({ section, isEducation = false, saving, error, onSave, onCancel, onDirtyChange }) {
    const baseId = useId()
    const [draft, setDraft] = useState(section)
    const [headingTouched, setHeadingTouched] = useState(false)
    const def = isEducation ? EDUCATION : TEMPLATES[section.template]
    const Editor = isEducation ? EducationEditor : EDITORS[section.template]

    const errors = useMemo(() => validateSection(draft, { isEducation }), [draft, isEducation])
    const problems = Object.keys(errors).length + pendingEndDates(draft)
    const dirty = useMemo(() => JSON.stringify(stripKeys(draft)) !== JSON.stringify(stripKeys(section)), [draft, section])

    useEffect(() => {
        onDirtyChange?.(dirty)
    }, [dirty, onDirtyChange])
    useEffect(() => () => onDirtyChange?.(false), [onDirtyChange])

    const Icon = def.icon

    return (
        <div className={styles.editor}>
            <FormError message={error?.message} lines={error?.lines} />
            <div className={styles.topRow}>
                {isEducation ? (
                    <div>
                        <span className={ui.label}>Section</span>
                        <div className={styles.templateTag} style={{ marginTop: '0.35rem' }}>
                            Education
                        </div>
                    </div>
                ) : (
                    <Field label="Section heading" htmlFor={`${baseId}-heading`} error={headingTouched ? errors.heading : undefined}>
                        <input
                            id={`${baseId}-heading`}
                            className={ui.input}
                            value={draft.heading}
                            onChange={(e) => setDraft((d) => ({ ...d, heading: e.target.value }))}
                            onBlur={() => setHeadingTouched(true)}
                            placeholder={section.template === 'cards' ? 'Projects' : 'Section heading'}
                        />
                    </Field>
                )}
                <div className={styles.templateTag} title="The template cannot be changed after the section is created.">
                    <Icon size={16} aria-hidden="true" /> {isEducation ? 'Timeline' : def.label}
                </div>
            </div>
            <label className={styles.inline}>
                <input type="checkbox" checked={draft.visible} onChange={(e) => setDraft((d) => ({ ...d, visible: e.target.checked }))} />
                Show on profile
            </label>

            <Editor items={draft.data} onChange={(data) => setDraft((d) => ({ ...d, data }))} errors={errors} idPrefix={baseId} />

            <div className={styles.actions}>
                {problems > 0 && (
                    <span className={styles.attention} role="status">
                        {problems} {problems === 1 ? 'field needs' : 'fields need'} attention before you can save.
                    </span>
                )}
                <button type="button" className="btn outlined" onClick={onCancel} disabled={saving}>
                    Cancel
                </button>
                <button type="button" className="btn contained" onClick={() => onSave(draft)} disabled={saving || problems > 0}>
                    {saving ? <Loader2 size={16} className="spin" aria-hidden="true" /> : <Save size={16} aria-hidden="true" />}
                    {saving ? 'Saving…' : 'Save section'}
                </button>
            </div>
        </div>
    )
}
