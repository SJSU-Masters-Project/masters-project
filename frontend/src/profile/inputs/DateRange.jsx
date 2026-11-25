import React from 'react'
import { Field } from '../../ui'
import { isoToMonth, monthToIso } from '../dates'
import ui from '../../ui.module.css'
import styles from '../editors/editors.module.css'

// Start and end months. Ticking the checkbox stores endDate as null, which is shown as "Present".
// While the box is empty and unticked the end date is held as '' (not yet chosen) until the user picks a month.
export default function DateRange({ idPrefix, startDate, endDate, onChange, currentLabel, errors = {} }) {
    const current = endDate === null
    return (
        <div className={styles.dates}>
            <Field label="Start date" htmlFor={`${idPrefix}-start`} error={errors.startDate}>
                <input
                    id={`${idPrefix}-start`}
                    type="month"
                    className={ui.input}
                    value={isoToMonth(startDate)}
                    onChange={(e) => onChange({ startDate: monthToIso(e.target.value), endDate })}
                />
            </Field>
            <Field
                label="End date"
                htmlFor={`${idPrefix}-end`}
                error={errors.endDate || (endDate === '' ? `Choose an end date, or tick "${currentLabel}".` : undefined)}
            >
                <input
                    id={`${idPrefix}-end`}
                    type="month"
                    className={ui.input}
                    value={current ? '' : isoToMonth(endDate)}
                    disabled={current}
                    onChange={(e) => onChange({ startDate, endDate: e.target.value ? monthToIso(e.target.value) : '' })}
                />
            </Field>
            <label className={`${styles.inline} ${styles.dateCheck}`}>
                <input type="checkbox" checked={current} onChange={(e) => onChange({ startDate, endDate: e.target.checked ? null : '' })} />
                {currentLabel}
            </label>
        </div>
    )
}
