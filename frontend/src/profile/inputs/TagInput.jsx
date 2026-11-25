import React, { useState } from 'react'
import { X } from 'lucide-react'
import styles from '../editors/editors.module.css'

// Free-text tags. Enter or a comma adds the typed text; duplicates (ignoring case) are skipped.
export default function TagInput({ id, value, onChange, placeholder, label }) {
    const [draft, setDraft] = useState('')

    const add = (text) => {
        const tag = text.trim()
        setDraft('')
        if (!tag || value.some((v) => v.toLowerCase() === tag.toLowerCase())) return
        onChange([...value, tag])
    }

    const onKeyDown = (e) => {
        if (e.key === 'Enter' || e.key === ',') {
            e.preventDefault()
            add(draft)
        } else if (e.key === 'Backspace' && draft === '' && value.length > 0) {
            onChange(value.slice(0, -1))
        }
    }

    const onChangeText = (e) => {
        const text = e.target.value
        if (text.includes(',')) {
            const parts = text.split(',')
            const last = parts.pop()
            const next = [...value]
            for (const p of parts) {
                const tag = p.trim()
                if (tag && !next.some((v) => v.toLowerCase() === tag.toLowerCase())) next.push(tag)
            }
            onChange(next)
            setDraft(last)
        } else setDraft(text)
    }

    return (
        <div className={styles.tagBox}>
            {value.map((tag, i) => (
                <span key={tag} className={styles.tagChip}>
                    {tag}
                    <button
                        type="button"
                        className={styles.tagRemove}
                        onClick={() => onChange(value.filter((_, j) => j !== i))}
                        aria-label={`Remove ${tag}`}
                    >
                        <X size={12} aria-hidden="true" />
                    </button>
                </span>
            ))}
            <input
                id={id}
                className={styles.tagText}
                value={draft}
                onChange={onChangeText}
                onKeyDown={onKeyDown}
                onBlur={() => add(draft)}
                placeholder={value.length === 0 ? placeholder : undefined}
                aria-label={label}
            />
        </div>
    )
}
