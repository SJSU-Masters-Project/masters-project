import React, { useId } from 'react'
import styles from '../editors/editors.module.css'

// A radio group for a whole number from 1 to 5. Arrow keys move between the options.
export default function ProficiencyInput({ value, onChange, label = 'Proficiency (1 to 5)' }) {
    const name = useId()
    return (
        <fieldset className={styles.proficiency}>
            <legend>{label}</legend>
            <div className={styles.scale}>
                {[1, 2, 3, 4, 5].map((n) => (
                    <label key={n} className={value === n ? styles.scaleOn : undefined}>
                        <input type="radio" name={name} value={n} checked={value === n} onChange={() => onChange(n)} />
                        <span>{n}</span>
                    </label>
                ))}
            </div>
        </fieldset>
    )
}
