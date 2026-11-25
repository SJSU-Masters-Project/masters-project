import React, { useEffect, useId, useState } from 'react'
import { Field, Dialog } from '../../ui'
import ui from '../../ui.module.css'
import { TEMPLATE_NAMES, TEMPLATES } from '../templates'
import styles from './editors.module.css'

// Asks for a heading and one of the six templates. The choice is final: a section's template is not editable later.
export default function AddSectionDialog({ open, onClose, onCreate }) {
    const id = useId()
    const [heading, setHeading] = useState('')
    const [template, setTemplate] = useState('cards')
    const [touched, setTouched] = useState(false)

    useEffect(() => {
        if (open) {
            setHeading('')
            setTemplate('cards')
            setTouched(false)
        }
    }, [open])

    const headingError = heading.trim() === '' ? 'Heading is required.' : undefined
    const create = () => {
        setTouched(true)
        if (headingError) return
        onCreate({ heading: heading.trim(), template })
    }

    return (
        <Dialog
            open={open}
            title="Add a section"
            onClose={onClose}
            maxWidth={560}
            actions={
                <>
                    <button type="button" className="btn outlined" onClick={onClose}>
                        Cancel
                    </button>
                    <button type="button" className="btn contained" onClick={create}>
                        Add section
                    </button>
                </>
            }
        >
            <Field label="Heading" htmlFor={`${id}-heading`} error={touched ? headingError : undefined}>
                <input
                    id={`${id}-heading`}
                    className={ui.input}
                    value={heading}
                    onChange={(e) => setHeading(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), create())}
                    placeholder="Projects"
                    autoFocus
                />
            </Field>
            <fieldset className={styles.templates}>
                <legend className={ui.label}>Template (cannot be changed later)</legend>
                {TEMPLATE_NAMES.map((name) => {
                    const t = TEMPLATES[name]
                    const Icon = t.icon
                    return (
                        <label key={name} className={`${styles.templateOption} ${template === name ? styles.templateOn : ''}`}>
                            <input
                                type="radio"
                                name={`${id}-template`}
                                value={name}
                                checked={template === name}
                                onChange={() => setTemplate(name)}
                            />
                            <Icon size={18} aria-hidden="true" />
                            <span>
                                <strong>{t.label}</strong>
                                <span className={styles.templateUse}>{t.useCase}</span>
                            </span>
                        </label>
                    )
                })}
            </fieldset>
        </Dialog>
    )
}
