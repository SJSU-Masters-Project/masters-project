import React from 'react'
import { Field } from '../../ui'
import ui from '../../ui.module.css'
import { withKeys } from '../adapters'
import ItemList from '../inputs/ItemList'
import LinesInput from '../inputs/LinesInput'
import TagInput from '../inputs/TagInput'
import { TEMPLATES } from '../templates'

export default function CardsEditor({ items, onChange, errors, idPrefix }) {
    return (
        <ItemList
            items={items}
            onChange={onChange}
            itemLabel="Card"
            addLabel="Add card"
            emptyMessage="No cards yet."
            makeItem={() => withKeys(TEMPLATES.cards.emptyItem())}
            renderItem={(item, i, update, show) => {
                const id = `${idPrefix}-${i}`
                const err = (f) => (show ? errors[`data.${i}.${f}`] : undefined)
                return (
                    <>
                        <Field label="Title" htmlFor={`${id}-title`} error={err('title')}>
                            <input
                                id={`${id}-title`}
                                className={ui.input}
                                value={item.title}
                                onChange={(e) => update({ title: e.target.value })}
                            />
                        </Field>
                        <Field label="Purpose (optional)" htmlFor={`${id}-purpose`} hint="A short summary.">
                            <textarea
                                id={`${id}-purpose`}
                                className={ui.textarea}
                                style={{ minHeight: 70 }}
                                value={item.purpose || ''}
                                onChange={(e) => update({ purpose: e.target.value })}
                            />
                        </Field>
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
                        <Field label="Tech stack (optional)" htmlFor={`${id}-tech`} hint="Press Enter or type a comma after each one.">
                            <TagInput
                                id={`${id}-tech`}
                                label="Add a technology"
                                value={item.techStack || []}
                                onChange={(techStack) => update({ techStack })}
                                placeholder="React, Node.js"
                            />
                        </Field>
                        <Field label="Features (optional)" htmlFor={`${id}-features`} hint="One per line.">
                            <LinesInput id={`${id}-features`} value={item.features || []} onChange={(features) => update({ features })} />
                        </Field>
                    </>
                )
            }}
        />
    )
}
