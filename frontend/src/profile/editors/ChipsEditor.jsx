import React from 'react'
import { Plus, Trash2 } from 'lucide-react'
import { Field } from '../../ui'
import ui from '../../ui.module.css'
import { withKeys } from '../adapters'
import ItemList from '../inputs/ItemList'
import ProficiencyInput from '../inputs/ProficiencyInput'
import { TEMPLATES } from '../templates'
import styles from './editors.module.css'

// One item is a category; it holds a list of skills, each with a 1 to 5 proficiency.
export default function ChipsEditor({ items, onChange, errors, idPrefix }) {
    return (
        <ItemList
            items={items}
            onChange={onChange}
            itemLabel="Category"
            addLabel="Add category"
            emptyMessage="No skill categories yet."
            makeItem={() => withKeys(TEMPLATES.chips.emptyItem())}
            renderItem={(item, i, update, show) => {
                const id = `${idPrefix}-${i}`
                const err = (f) => (show ? errors[`data.${i}.${f}`] : undefined)
                const skills = item.skillsList || []
                const setSkill = (j, patch) => update({ skillsList: skills.map((s, k) => (k === j ? { ...s, ...patch } : s)) })
                return (
                    <>
                        <Field label="Category" htmlFor={`${id}-cat`} error={err('category')}>
                            <input
                                id={`${id}-cat`}
                                className={ui.input}
                                value={item.category}
                                onChange={(e) => update({ category: e.target.value })}
                                placeholder="Frontend"
                            />
                        </Field>
                        {err('skillsList') && <span className={ui.fieldError}>{err('skillsList')}</span>}
                        {skills.map((skill, j) => (
                            <div key={skill._key || j} className={styles.skillRow}>
                                <Field label={`Skill ${j + 1}`} htmlFor={`${id}-s${j}`} error={err(`skillsList.${j}.skillName`)}>
                                    <input
                                        id={`${id}-s${j}`}
                                        className={ui.input}
                                        value={skill.skillName}
                                        onChange={(e) => setSkill(j, { skillName: e.target.value })}
                                        placeholder="React"
                                    />
                                </Field>
                                <ProficiencyInput
                                    label={`Proficiency for skill ${j + 1} (1 to 5)`}
                                    value={skill.proficiency}
                                    onChange={(proficiency) => setSkill(j, { proficiency })}
                                />
                                <button
                                    type="button"
                                    className={`${styles.tool} ${styles.toolDanger}`}
                                    onClick={() => update({ skillsList: skills.filter((_, k) => k !== j) })}
                                    disabled={skills.length <= 1}
                                    aria-label={`Remove skill ${j + 1}`}
                                >
                                    <Trash2 size={16} aria-hidden="true" />
                                </button>
                            </div>
                        ))}
                        <button
                            type="button"
                            className="btn outlined small"
                            onClick={() => update({ skillsList: [...skills, ...withKeys([{ skillName: '', proficiency: 3 }])] })}
                        >
                            <Plus size={14} aria-hidden="true" /> Add skill
                        </button>
                    </>
                )
            }}
        />
    )
}
