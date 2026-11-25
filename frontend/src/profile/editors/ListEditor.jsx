import React from 'react'
import { Field } from '../../ui'
import ui from '../../ui.module.css'
import { withKeys } from '../adapters'
import ItemList from '../inputs/ItemList'
import { TEMPLATES } from '../templates'

export default function ListEditor({ items, onChange, errors, idPrefix }) {
    return (
        <ItemList
            items={items}
            onChange={onChange}
            itemLabel="Item"
            addLabel="Add item"
            emptyMessage="No items yet."
            makeItem={() => withKeys(TEMPLATES.list.emptyItem())}
            renderItem={(item, i, update, show) => {
                const id = `${idPrefix}-${i}`
                const err = (f) => (show ? errors[`data.${i}.${f}`] : undefined)
                return (
                    <>
                        <div className={ui.formRow}>
                            <Field label="Title" htmlFor={`${id}-title`} error={err('title')}>
                                <input
                                    id={`${id}-title`}
                                    className={ui.input}
                                    value={item.title}
                                    onChange={(e) => update({ title: e.target.value })}
                                />
                            </Field>
                            <Field label="Issuer or publisher (optional)" htmlFor={`${id}-sub`}>
                                <input
                                    id={`${id}-sub`}
                                    className={ui.input}
                                    value={item.subtitle || ''}
                                    onChange={(e) => update({ subtitle: e.target.value })}
                                />
                            </Field>
                            <Field label="Date (optional)" htmlFor={`${id}-date`} error={err('date')}>
                                <input
                                    id={`${id}-date`}
                                    type="date"
                                    className={ui.input}
                                    value={item.date || ''}
                                    onChange={(e) => update({ date: e.target.value || null })}
                                />
                            </Field>
                        </div>
                        <Field
                            label="Verification link (optional)"
                            htmlFor={`${id}-link`}
                            error={err('link')}
                            hint="Starts with http:// or https://"
                        >
                            <input
                                id={`${id}-link`}
                                className={ui.input}
                                value={item.link || ''}
                                onChange={(e) => update({ link: e.target.value })}
                                inputMode="url"
                                placeholder="https://example.com/verify"
                            />
                        </Field>
                        <Field label="Description (optional)" htmlFor={`${id}-desc`}>
                            <textarea
                                id={`${id}-desc`}
                                className={ui.textarea}
                                style={{ minHeight: 70 }}
                                value={item.description || ''}
                                onChange={(e) => update({ description: e.target.value })}
                            />
                        </Field>
                    </>
                )
            }}
        />
    )
}
