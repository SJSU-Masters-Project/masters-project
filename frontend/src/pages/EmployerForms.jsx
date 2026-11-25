import React, { useEffect, useState } from 'react'
import { Plus, X } from 'lucide-react'
import { api } from '../api'
import { EMPLOYMENT_TYPES, WORK_MODES, detailLines } from '../format'
import { Dialog, Field, FormError } from '../ui'
import ui from '../ui.module.css'
import styles from './Employer.module.css'

function errorState(err, fallback) {
    return { message: err.message || fallback, lines: detailLines(err.details), fields: err.details || {} }
}

export function CompanyForm({ company, onSaved, onCancel }) {
    const [form, setForm] = useState({
        name: company?.name || '',
        website: company?.website || '',
        location: company?.location || '',
        description: company?.description || '',
    })
    const [saving, setSaving] = useState(false)
    const [error, setError] = useState(null)
    const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }))

    const submit = async (event) => {
        event.preventDefault()
        if (saving) return
        setSaving(true)
        setError(null)
        try {
            const body = {
                name: form.name.trim(),
                website: form.website.trim(),
                location: form.location.trim(),
                description: form.description,
            }
            const saved = company
                ? await api(`/companies/${company.id}`, { method: 'PATCH', body })
                : await api('/companies', { method: 'POST', body })
            onSaved(saved)
        } catch (err) {
            setError(errorState(err, 'Could not save the company.'))
        } finally {
            setSaving(false)
        }
    }

    return (
        <form onSubmit={submit}>
            <FormError message={error?.message} lines={error?.lines} />
            <div className={ui.formRow}>
                <Field label="Company name" htmlFor="co-name">
                    <input
                        id="co-name"
                        className={ui.input}
                        value={form.name}
                        onChange={set('name')}
                        minLength={2}
                        maxLength={150}
                        required
                    />
                </Field>
                <Field label="Location" htmlFor="co-loc">
                    <input id="co-loc" className={ui.input} value={form.location} onChange={set('location')} maxLength={200} />
                </Field>
            </div>
            <Field label="Website" htmlFor="co-site" hint="Include https://">
                <input
                    id="co-site"
                    className={ui.input}
                    type="url"
                    value={form.website}
                    onChange={set('website')}
                    placeholder="https://example.com"
                />
            </Field>
            <Field label="About the company" htmlFor="co-desc">
                <textarea id="co-desc" className={ui.textarea} value={form.description} onChange={set('description')} maxLength={5000} />
            </Field>
            <div className={styles.formActions}>
                {onCancel && (
                    <button type="button" className="btn outlined" onClick={onCancel} disabled={saving}>
                        Cancel
                    </button>
                )}
                <button type="submit" className="btn contained" disabled={saving || form.name.trim().length < 2}>
                    {saving ? 'Saving…' : company ? 'Save company' : 'Create company'}
                </button>
            </div>
        </form>
    )
}

const emptyJob = {
    title: '',
    description: '',
    location: '',
    work_mode: 'hybrid',
    employment_type: 'full_time',
    openings: 1,
    skills: [{ name: '', required: true }],
}

const fromJob = (job) => (job ? { ...job, skills: job.skills.map((s) => ({ name: s.name, required: s.required })) } : emptyJob)

export function JobFormDialog({ open, job, onClose, onSaved }) {
    const [form, setForm] = useState(emptyJob)
    const [saving, setSaving] = useState(false)
    const [error, setError] = useState(null)

    useEffect(() => {
        if (open) {
            setForm(fromJob(job))
            setError(null)
        }
    }, [open, job])

    const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }))
    const setSkill = (i, patch) => setForm((f) => ({ ...f, skills: f.skills.map((s, idx) => (idx === i ? { ...s, ...patch } : s)) }))
    const addSkill = () => setForm((f) => ({ ...f, skills: [...f.skills, { name: '', required: false }] }))
    const removeSkill = (i) => setForm((f) => ({ ...f, skills: f.skills.filter((_, idx) => idx !== i) }))

    const submit = async (event) => {
        event.preventDefault()
        if (saving) return
        setSaving(true)
        setError(null)
        try {
            const body = {
                title: form.title.trim(),
                description: form.description.trim(),
                location: form.location.trim(),
                work_mode: form.work_mode,
                employment_type: form.employment_type,
                openings: Number(form.openings) || 1,
                skills: form.skills.map((s) => ({ name: s.name.trim(), required: s.required })).filter((s) => s.name),
            }
            const saved = job ? await api(`/jobs/${job.id}`, { method: 'PATCH', body }) : await api('/jobs', { method: 'POST', body })
            onSaved(saved)
        } catch (err) {
            setError(errorState(err, 'Could not save the job.'))
        } finally {
            setSaving(false)
        }
    }

    const fieldError = (name) => {
        const first = error?.fields?.[name]?.[0]
        return typeof first === 'string' ? first : undefined
    }
    const hasRequired = form.skills.some((s) => s.required && s.name.trim())

    return (
        <Dialog
            open={open}
            title={job ? 'Edit job' : 'Post a job'}
            onClose={() => !saving && onClose()}
            maxWidth={720}
            actions={
                <>
                    <button type="button" className="btn outlined" onClick={onClose} disabled={saving}>
                        Cancel
                    </button>
                    <button type="submit" form="job-form" className="btn contained" disabled={saving || !form.title.trim() || !hasRequired}>
                        {saving ? 'Saving…' : job ? 'Save changes' : 'Save as draft'}
                    </button>
                </>
            }
        >
            <form id="job-form" onSubmit={submit}>
                <FormError message={error?.message} lines={error?.lines} />
                <Field label="Title" htmlFor="job-title" error={fieldError('title')}>
                    <input
                        id="job-title"
                        className={ui.input}
                        value={form.title}
                        onChange={set('title')}
                        minLength={3}
                        maxLength={150}
                        required
                    />
                </Field>
                <div className={ui.formRow}>
                    <Field label="Employment type" htmlFor="job-type">
                        <select id="job-type" className={ui.select} value={form.employment_type} onChange={set('employment_type')}>
                            {EMPLOYMENT_TYPES.map((o) => (
                                <option key={o.value} value={o.value}>
                                    {o.label}
                                </option>
                            ))}
                        </select>
                    </Field>
                    <Field label="Work mode" htmlFor="job-mode">
                        <select id="job-mode" className={ui.select} value={form.work_mode} onChange={set('work_mode')}>
                            {WORK_MODES.map((o) => (
                                <option key={o.value} value={o.value}>
                                    {o.label}
                                </option>
                            ))}
                        </select>
                    </Field>
                    <Field label="Location" htmlFor="job-loc">
                        <input id="job-loc" className={ui.input} value={form.location || ''} onChange={set('location')} maxLength={200} />
                    </Field>
                    <Field label="Openings" htmlFor="job-open" error={fieldError('openings')}>
                        <input
                            id="job-open"
                            className={ui.input}
                            type="number"
                            min={1}
                            max={100}
                            value={form.openings}
                            onChange={set('openings')}
                        />
                    </Field>
                </div>
                <Field label="Description" htmlFor="job-desc" hint="At least 50 characters." error={fieldError('description')}>
                    <textarea
                        id="job-desc"
                        className={ui.textarea}
                        value={form.description}
                        onChange={set('description')}
                        minLength={50}
                        maxLength={20000}
                        required
                    />
                </Field>

                <div className={ui.field}>
                    <span className={ui.label}>Skills (mark at least one as required)</span>
                    {fieldError('skills') && <span className={ui.fieldError}>{fieldError('skills')}</span>}
                    {form.skills.map((s, i) => (
                        <div key={i} className={styles.skillRow}>
                            <input
                                className={ui.input}
                                value={s.name}
                                onChange={(e) => setSkill(i, { name: e.target.value })}
                                placeholder="e.g. Python"
                                maxLength={100}
                                aria-label={`Skill ${i + 1}`}
                            />
                            <label className={styles.reqToggle}>
                                <input type="checkbox" checked={s.required} onChange={(e) => setSkill(i, { required: e.target.checked })} />{' '}
                                Required
                            </label>
                            <button
                                type="button"
                                className="shell-icon-btn"
                                onClick={() => removeSkill(i)}
                                disabled={form.skills.length === 1}
                                aria-label={`Remove skill ${i + 1}`}
                            >
                                <X size={16} />
                            </button>
                        </div>
                    ))}
                    <div>
                        <button type="button" className="btn outlined small" onClick={addSkill} disabled={form.skills.length >= 50}>
                            <Plus size={14} aria-hidden="true" /> Add skill
                        </button>
                    </div>
                </div>
            </form>
        </Dialog>
    )
}
