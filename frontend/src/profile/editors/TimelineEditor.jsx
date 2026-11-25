import React from 'react'
import { Field } from '../../ui'
import ui from '../../ui.module.css'
import { withKeys } from '../adapters'
import DateRange from '../inputs/DateRange'
import ItemList from '../inputs/ItemList'
import { EDUCATION, TEMPLATES } from '../templates'

// Edits the timeline template. With `education`, the items use degree / institute / grade.
export default function TimelineEditor({ items, onChange, errors, idPrefix, education = false }) {
    const def = education ? EDUCATION : TEMPLATES.timeline
    return (
        <ItemList
            items={items}
            onChange={onChange}
            itemLabel={education ? 'Education entry' : 'Entry'}
            addLabel={education ? 'Add education' : 'Add entry'}
            emptyMessage={education ? 'No education added yet.' : 'No entries yet.'}
            makeItem={() => withKeys(def.emptyItem())}
            renderItem={(item, i, update, show) => {
                const id = `${idPrefix}-${i}`
                const err = (f) => (show ? errors[`data.${i}.${f}`] : undefined)
                const dateErrors = { startDate: err('startDate'), endDate: err('endDate') }
                return (
                    <>
                        <div className={ui.formRow}>
                            <Field label={education ? 'Degree' : 'Title'} htmlFor={`${id}-a`} error={err(education ? 'degree' : 'title')}>
                                <input
                                    id={`${id}-a`}
                                    className={ui.input}
                                    value={(education ? item.degree : item.title) || ''}
                                    onChange={(e) => update(education ? { degree: e.target.value } : { title: e.target.value })}
                                    placeholder={education ? 'MS Software Engineering' : 'Software Engineering Intern'}
                                />
                            </Field>
                            <Field
                                label={education ? 'Institute' : 'Company or organization'}
                                htmlFor={`${id}-b`}
                                error={err(education ? 'institute' : 'subtitle')}
                            >
                                <input
                                    id={`${id}-b`}
                                    className={ui.input}
                                    value={(education ? item.institute : item.subtitle) || ''}
                                    onChange={(e) => update(education ? { institute: e.target.value } : { subtitle: e.target.value })}
                                />
                            </Field>
                        </div>
                        <DateRange
                            idPrefix={id}
                            startDate={item.startDate}
                            endDate={item.endDate}
                            onChange={update}
                            currentLabel={education ? 'I currently study here' : 'I currently work here'}
                            errors={dateErrors}
                        />
                        {education ? (
                            <Field label="Grade (optional)" htmlFor={`${id}-grade`}>
                                <input
                                    id={`${id}-grade`}
                                    className={ui.input}
                                    value={item.grade || ''}
                                    onChange={(e) => update({ grade: e.target.value })}
                                    placeholder="3.9 GPA"
                                />
                            </Field>
                        ) : (
                            <Field label="Description (optional)" htmlFor={`${id}-desc`} hint="Responsibilities and achievements.">
                                <textarea
                                    id={`${id}-desc`}
                                    className={ui.textarea}
                                    value={item.description || ''}
                                    onChange={(e) => update({ description: e.target.value })}
                                />
                            </Field>
                        )}
                        <Field label="Link (optional)" htmlFor={`${id}-link`} error={err('link')} hint="Starts with http:// or https://">
                            <input
                                id={`${id}-link`}
                                className={ui.input}
                                value={item.link || ''}
                                onChange={(e) => update({ link: e.target.value })}
                                inputMode="url"
                                placeholder="https://example.com"
                            />
                        </Field>
                    </>
                )
            }}
        />
    )
}
