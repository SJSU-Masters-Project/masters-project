import React from 'react'
import { Field } from '../../ui'
import ui from '../../ui.module.css'
import { withKeys } from '../adapters'
import ItemList from '../inputs/ItemList'
import { TEMPLATES } from '../templates'

export default function LinksEditor({ items, onChange, errors, idPrefix }) {
    return (
        <ItemList
            items={items}
            onChange={onChange}
            itemLabel="Link"
            addLabel="Add link"
            emptyMessage="No links yet."
            makeItem={() => withKeys(TEMPLATES.links.emptyItem())}
            renderItem={(item, i, update, show) => {
                const id = `${idPrefix}-${i}`
                const err = (f) => (show ? errors[`data.${i}.${f}`] : undefined)
                return (
                    <>
                        <div className={ui.formRow}>
                            <Field label="Name" htmlFor={`${id}-name`} error={err('name')}>
                                <input
                                    id={`${id}-name`}
                                    className={ui.input}
                                    value={item.name}
                                    onChange={(e) => update({ name: e.target.value })}
                                />
                            </Field>
                            <Field label="URL" htmlFor={`${id}-url`} error={err('url')} hint="Starts with http:// or https://">
                                <input
                                    id={`${id}-url`}
                                    className={ui.input}
                                    value={item.url}
                                    onChange={(e) => update({ url: e.target.value })}
                                    inputMode="url"
                                    placeholder="https://github.com/you"
                                />
                            </Field>
                        </div>
                        <Field label="Note (optional)" htmlFor={`${id}-desc`}>
                            <input
                                id={`${id}-desc`}
                                className={ui.input}
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
