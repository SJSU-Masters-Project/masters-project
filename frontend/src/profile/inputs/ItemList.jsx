import React, { useState } from 'react'
import { ArrowDown, ArrowUp, Plus, Trash2 } from 'lucide-react'
import styles from '../editors/editors.module.css'

const swap = (list, a, b) => {
    const next = [...list]
    ;[next[a], next[b]] = [next[b], next[a]]
    return next
}

// A list of editable items with add, remove and move up/down buttons (no drag and drop).
//   renderItem(item, index, update, show) -> the fields for one item
//     update(patch) merges a patch into the item; `show` is true once the user has left the item,
//     which is when its "required" messages start to appear.
export default function ItemList({ items, onChange, renderItem, makeItem, itemLabel, addLabel, emptyMessage, minItems = 0 }) {
    const [touched, setTouched] = useState(() => new Set())
    const markTouched = (key) => setTouched((t) => (t.has(key) ? t : new Set(t).add(key)))

    const update = (index, patch) => onChange(items.map((it, i) => (i === index ? { ...it, ...patch } : it)))

    return (
        <div>
            {items.length === 0 && emptyMessage && <p className={styles.empty}>{emptyMessage}</p>}
            <ol className={styles.items}>
                {items.map((item, i) => {
                    const key = item._key || i
                    return (
                        <li
                            key={key}
                            className={styles.itemBox}
                            onBlur={(e) => !e.currentTarget.contains(e.relatedTarget) && markTouched(key)}
                        >
                            <div className={styles.itemBar}>
                                <span className={styles.itemName}>
                                    {itemLabel} {i + 1}
                                </span>
                                <span className={styles.itemTools}>
                                    <button
                                        type="button"
                                        className={styles.tool}
                                        onClick={() => onChange(swap(items, i, i - 1))}
                                        disabled={i === 0}
                                        aria-label={`Move ${itemLabel} ${i + 1} up`}
                                    >
                                        <ArrowUp size={16} aria-hidden="true" />
                                    </button>
                                    <button
                                        type="button"
                                        className={styles.tool}
                                        onClick={() => onChange(swap(items, i, i + 1))}
                                        disabled={i === items.length - 1}
                                        aria-label={`Move ${itemLabel} ${i + 1} down`}
                                    >
                                        <ArrowDown size={16} aria-hidden="true" />
                                    </button>
                                    <button
                                        type="button"
                                        className={`${styles.tool} ${styles.toolDanger}`}
                                        onClick={() => onChange(items.filter((_, j) => j !== i))}
                                        disabled={items.length <= minItems}
                                        aria-label={`Remove ${itemLabel} ${i + 1}`}
                                    >
                                        <Trash2 size={16} aria-hidden="true" />
                                    </button>
                                </span>
                            </div>
                            {renderItem(item, i, (patch) => update(i, patch), touched.has(key))}
                        </li>
                    )
                })}
            </ol>
            <div className={styles.addRow} style={items.length ? { marginTop: '0.9rem' } : undefined}>
                <button type="button" className="btn outlined small" onClick={() => onChange([...items, makeItem()])}>
                    <Plus size={14} aria-hidden="true" /> {addLabel}
                </button>
            </div>
        </div>
    )
}
