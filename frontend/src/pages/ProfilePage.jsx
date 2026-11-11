import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { Loader2, Plus, Save, UserRound } from 'lucide-react'
import { api } from '../api'
import { EMPLOYMENT_TYPES, WORK_MODES, detailLines } from '../format'
import { blankForm, deriveSkills, fromProfile, toBody, toEducationPatch, toForm, toSectionsPatch, withKeys } from '../profile/adapters'
import AddSectionDialog from '../profile/editors/AddSectionDialog'
import SectionEditor from '../profile/editors/SectionEditor'
import SectionCard from '../profile/SectionCard'
import { newEducation, newSection } from '../profile/templates'
import { Dialog, EmptyState, ErrorState, Field, FormError, LoginRequired, Page, PageHeader, Pill, SkeletonGrid, Toast, cx } from '../ui'
import { useSession } from '../session'
import ui from '../ui.module.css'
import styles from './Profile.module.css'

function CheckGroup({ options, value, onChange, legend }) {
    const toggle = (v) => onChange(value.includes(v) ? value.filter((x) => x !== v) : [...value, v])
    return (
        <div className={ui.checkGroup} role="group" aria-label={legend}>
            {options.map((o) => (
                <label key={o.value} className={cx(ui.check, value.includes(o.value) && ui.checkOn)}>
                    <input type="checkbox" checked={value.includes(o.value)} onChange={() => toggle(o.value)} />
                    {o.label}
                </label>
            ))}
        </div>
    )
}

const EDUCATION_EDITOR = 'education'

export default function ProfilePage() {
    const { user, isLoggedIn, isCandidate } = useSession()
    const [existing, setExisting] = useState(null)
    const [resumes, setResumes] = useState([])
    const [form, setForm] = useState(blankForm)
    const [sections, setSections] = useState([])
    const [education, setEducation] = useState(null)
    const [loading, setLoading] = useState(true)
    const [loadError, setLoadError] = useState(null)
    const [saving, setSaving] = useState(false)
    const [saveError, setSaveError] = useState(null)
    const [toast, setToast] = useState(null)

    // Section editing: `editing` is a section's _key (or EDUCATION_EDITOR); `pending` is a section that is not saved yet.
    const [editing, setEditing] = useState(null)
    const [pending, setPending] = useState(null)
    const [editorSaving, setEditorSaving] = useState(false)
    const [editorError, setEditorError] = useState(null)
    const [busyKey, setBusyKey] = useState(null)
    const [addOpen, setAddOpen] = useState(false)
    const [toDelete, setToDelete] = useState(null)
    const [editorDirty, setEditorDirty] = useState(false)

    const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.type === 'checkbox' ? e.target.checked : e.target.value }))

    const apply = useCallback((profile) => {
        const parts = fromProfile(profile)
        setExisting(profile)
        setForm(toForm(profile))
        setSections(parts.sections)
        setEducation(parts.education)
    }, [])

    const load = useCallback(async () => {
        setLoading(true)
        setLoadError(null)
        try {
            const [profile, list] = await Promise.all([
                api('/profiles/me').catch((err) => {
                    if (err.code === 'profile_not_found') return null
                    throw err
                }),
                api('/resumes', { params: { limit: 100 } }),
            ])
            setResumes(list.items)
            if (profile) apply(profile)
            else {
                setExisting(null)
                setForm(blankForm)
                setSections([])
                setEducation(null)
            }
        } catch (err) {
            setLoadError(err.message || 'Unable to load your profile. Please try again later.')
        } finally {
            setLoading(false)
        }
    }, [apply])

    useEffect(() => {
        if (isLoggedIn && isCandidate) load()
        else setLoading(false)
    }, [isLoggedIn, isCandidate, load])

    const closeToast = useCallback(() => setToast(null), [])

    // Unsaved edits: the details form differs from what was saved, or a section editor has changes.
    const formDirty = useMemo(() => JSON.stringify(form) !== JSON.stringify(existing ? toForm(existing) : blankForm), [form, existing])
    const dirty = formDirty || editorDirty
    useEffect(() => {
        if (!dirty) return undefined
        const warn = (e) => {
            e.preventDefault()
            e.returnValue = ''
        }
        window.addEventListener('beforeunload', warn)
        return () => window.removeEventListener('beforeunload', warn)
    }, [dirty])

    const save = async () => {
        if (saving) return
        setSaving(true)
        setSaveError(null)
        try {
            const body = toBody(form, sections, education, existing, user.email)
            const saved = await api('/profiles/me', { method: existing ? 'PATCH' : 'PUT', body })
            apply(saved)
            setToast({ severity: 'success', message: 'Profile saved.' })
        } catch (err) {
            setSaveError({ message: err.message || 'Could not save your profile.', lines: detailLines(err.details) })
        } finally {
            setSaving(false)
        }
    }

    const closeEditor = () => {
        setEditing(null)
        setPending(null)
        setEditorError(null)
        setEditorDirty(false)
    }

    // Saves a new array of sections (create, edit, hide, move, delete all go through here).
    const patchSections = async (next) => {
        const saved = await api('/profiles/me', { method: 'PATCH', body: toSectionsPatch(next, existing) })
        apply(saved)
    }

    const saveSectionFromEditor = async (draft) => {
        setEditorSaving(true)
        setEditorError(null)
        try {
            if (editing === EDUCATION_EDITOR) {
                const saved = await api('/profiles/me', { method: 'PATCH', body: toEducationPatch(draft) })
                apply(saved)
            } else if (pending) {
                await patchSections([...sections, draft])
            } else {
                await patchSections(sections.map((s) => (s._key === draft._key ? draft : s)))
            }
            closeEditor()
            setToast({ severity: 'success', message: 'Section saved.' })
        } catch (err) {
            setEditorError({ message: err.message || 'Could not save this section.', lines: detailLines(err.details) })
        } finally {
            setEditorSaving(false)
        }
    }

    // Card actions that save straight away. Failures show a toast and leave the page as it was.
    const quickChange = async (key, run, successMessage) => {
        if (busyKey) return
        setBusyKey(key)
        try {
            await run()
            if (successMessage) setToast({ severity: 'success', message: successMessage })
        } catch (err) {
            setToast({ severity: 'error', message: err.message || 'Could not update your profile.' })
        } finally {
            setBusyKey(null)
        }
    }

    const toggleVisible = (section) =>
        quickChange(
            section._key,
            () => patchSections(sections.map((s) => (s._key === section._key ? { ...s, visible: !s.visible } : s))),
            section.visible ? `${section.heading} is now hidden.` : `${section.heading} is now shown.`
        )

    const toggleEducationVisible = () =>
        quickChange(EDUCATION_EDITOR, async () => {
            const saved = await api('/profiles/me', {
                method: 'PATCH',
                body: toEducationPatch({ ...education, visible: !education.visible }),
            })
            apply(saved)
        })

    const move = (index, delta) => {
        const next = [...sections]
        ;[next[index], next[index + delta]] = [next[index + delta], next[index]]
        quickChange(sections[index]._key, () => patchSections(next))
    }

    const confirmDelete = async () => {
        const target = toDelete
        setToDelete(null)
        await quickChange(
            target._key,
            () => patchSections(sections.filter((s) => s._key !== target._key)),
            `${target.heading} was deleted.`
        )
    }

    const startAdd = ({ heading, template }) => {
        const section = withKeys(newSection(template, heading))
        setAddOpen(false)
        setEditorError(null)
        setPending(section)
        setEditing(section._key)
    }

    const startEducation = () => {
        setEditorError(null)
        setEditing(EDUCATION_EDITOR)
    }

    const hasProfile = Boolean(existing)
    const skills = useMemo(() => deriveSkills(sections), [sections])

    const renderSection = (section, index) => {
        if (editing === section._key) {
            return (
                <div key={section._key} className={ui.card}>
                    <h2 className={ui.sectionTitle}>Edit {section.heading}</h2>
                    <SectionEditor
                        section={section}
                        saving={editorSaving}
                        error={editorError}
                        onSave={saveSectionFromEditor}
                        onCancel={closeEditor}
                        onDirtyChange={setEditorDirty}
                    />
                </div>
            )
        }
        return (
            <SectionCard
                key={section._key}
                section={section}
                busy={busyKey === section._key || editorSaving || editing !== null}
                isFirst={index === 0}
                isLast={index === sections.length - 1}
                onEdit={() => {
                    setEditorError(null)
                    setPending(null)
                    setEditing(section._key)
                }}
                onToggleVisible={() => toggleVisible(section)}
                onMove={(delta) => move(index, delta)}
                onDelete={() => setToDelete(section)}
            />
        )
    }

    let educationBlock
    if (editing === EDUCATION_EDITOR) {
        educationBlock = (
            <div className={ui.card}>
                <h2 className={ui.sectionTitle}>Edit Education</h2>
                <SectionEditor
                    section={education || withKeys(newEducation())}
                    isEducation
                    saving={editorSaving}
                    error={editorError}
                    onSave={saveSectionFromEditor}
                    onCancel={closeEditor}
                    onDirtyChange={setEditorDirty}
                />
            </div>
        )
    } else if (education) {
        educationBlock = (
            <SectionCard
                section={education}
                education
                busy={busyKey === EDUCATION_EDITOR || editorSaving || editing !== null}
                onEdit={startEducation}
                onToggleVisible={toggleEducationVisible}
            />
        )
    } else {
        educationBlock = (
            <section className={ui.card}>
                <h2 className={ui.sectionTitle}>Education</h2>
                <p className={ui.hint} style={{ marginBottom: '0.75rem' }}>
                    You have not added any education yet.
                </p>
                <button type="button" className="btn outlined" onClick={startEducation} disabled={!hasProfile || editing !== null}>
                    <Plus size={16} aria-hidden="true" /> Add education
                </button>
            </section>
        )
    }

    let body
    if (!isLoggedIn) body = <LoginRequired message="Please log in to edit your profile." />
    else if (!isCandidate) body = <EmptyState>Profiles are available to student and candidate accounts.</EmptyState>
    else if (loading) body = <SkeletonGrid count={2} height={260} />
    else if (loadError) body = <ErrorState message={loadError} onRetry={load} />
    else
        body = (
            <div className={styles.form}>
                <FormError message={saveError?.message} lines={saveError?.lines} />

                <section className={ui.card}>
                    <h2 className={ui.sectionTitle}>About you</h2>
                    <div className={ui.formRow}>
                        <Field label="Full name" htmlFor="pf-name">
                            <input
                                id="pf-name"
                                className={ui.input}
                                value={form.fullName}
                                onChange={set('fullName')}
                                maxLength={200}
                                required
                            />
                        </Field>
                        <Field label="Email" htmlFor="pf-email" hint="Taken from your account.">
                            <input id="pf-email" className={ui.input} value={existing?.personal?.email || user.email} disabled />
                        </Field>
                        <Field label="Phone" htmlFor="pf-phone">
                            <input
                                id="pf-phone"
                                className={ui.input}
                                value={form.phone}
                                onChange={set('phone')}
                                maxLength={30}
                                autoComplete="tel"
                            />
                        </Field>
                        <Field label="Location" htmlFor="pf-loc">
                            <input
                                id="pf-loc"
                                className={ui.input}
                                value={form.location}
                                onChange={set('location')}
                                maxLength={200}
                                placeholder="San Jose, CA"
                            />
                        </Field>
                    </div>
                </section>

                <section className={ui.card}>
                    <h2 className={ui.sectionTitle}>Career</h2>
                    <Field label="Headline" htmlFor="pf-headline">
                        <input
                            id="pf-headline"
                            className={ui.input}
                            value={form.headline}
                            onChange={set('headline')}
                            maxLength={220}
                            placeholder="Graduate student seeking frontend engineering roles"
                        />
                    </Field>
                    <Field label="Summary" htmlFor="pf-summary">
                        <textarea id="pf-summary" className={ui.textarea} value={form.summary} onChange={set('summary')} maxLength={3000} />
                    </Field>
                    <div className={ui.field}>
                        <span className={ui.label}>Skills</span>
                        {skills.length > 0 ? (
                            <ul className={styles.skillList} aria-label="Skills from your skill sections">
                                {skills.map((s) => (
                                    <li key={s}>
                                        <Pill>{s}</Pill>
                                    </li>
                                ))}
                            </ul>
                        ) : null}
                        <span className={ui.hint}>
                            Skills come from the skill sections below, so matching always uses what you show on your profile.
                            {skills.length === 0 && ' Add a Skill chips section to list yours.'}
                        </span>
                    </div>
                    <Field
                        label="Resume linked to your profile"
                        htmlFor="pf-resume"
                        hint={resumes.length === 0 ? 'Upload a resume on the Resumes page to link it here.' : undefined}
                    >
                        <select id="pf-resume" className={ui.select} value={form.resumeId} onChange={set('resumeId')}>
                            <option value="">None</option>
                            {resumes.map((r) => (
                                <option key={r.id} value={r.id}>
                                    {r.filename}
                                </option>
                            ))}
                        </select>
                    </Field>
                </section>

                {!hasProfile && (
                    <p className={ui.hint}>Create your profile first. Education and custom sections can be added right after.</p>
                )}

                <div className={styles.sections}>
                    {educationBlock}
                    {sections.map(renderSection)}
                    {pending && (
                        <div className={ui.card}>
                            <h2 className={ui.sectionTitle}>New section</h2>
                            <SectionEditor
                                section={pending}
                                saving={editorSaving}
                                error={editorError}
                                onSave={saveSectionFromEditor}
                                onCancel={closeEditor}
                                onDirtyChange={setEditorDirty}
                            />
                        </div>
                    )}
                    {hasProfile && sections.length === 0 && !pending && (
                        <p className={ui.hint}>
                            Add sections such as projects, experience, certifications, skills, links or a short introduction.
                        </p>
                    )}
                </div>

                <section className={ui.card}>
                    <h2 className={ui.sectionTitle}>Job preferences</h2>
                    <Field label="Target roles" htmlFor="pf-roles" hint="Separate with commas.">
                        <input
                            id="pf-roles"
                            className={ui.input}
                            value={form.targetRoles}
                            onChange={set('targetRoles')}
                            placeholder="Frontend Engineer, Software Engineer"
                        />
                    </Field>
                    <div className={ui.field}>
                        <span className={ui.label}>Employment types</span>
                        <CheckGroup
                            legend="Employment types"
                            options={EMPLOYMENT_TYPES}
                            value={form.employmentTypes}
                            onChange={(v) => setForm((f) => ({ ...f, employmentTypes: v }))}
                        />
                    </div>
                    <div className={ui.field}>
                        <span className={ui.label}>Work modes</span>
                        <CheckGroup
                            legend="Work modes"
                            options={WORK_MODES}
                            value={form.workModes}
                            onChange={(v) => setForm((f) => ({ ...f, workModes: v }))}
                        />
                    </div>
                    <Field label="Preferred locations" htmlFor="pf-locs" hint="Separate with commas.">
                        <input
                            id="pf-locs"
                            className={ui.input}
                            value={form.preferredLocations}
                            onChange={set('preferredLocations')}
                            placeholder="San Francisco Bay Area, Remote - US"
                        />
                    </Field>
                    <label className={styles.inline}>
                        <input type="checkbox" checked={form.willingToRelocate} onChange={set('willingToRelocate')} /> Willing to relocate
                    </label>
                </section>

                <section className={ui.card}>
                    <h2 className={ui.sectionTitle}>Visibility</h2>
                    <Field
                        label="Who can see your profile"
                        htmlFor="pf-vis"
                        hint="Public profiles show your name, location, education and career details to logged-in users. Contact details stay private."
                    >
                        <select id="pf-vis" className={ui.select} value={form.visibility} onChange={set('visibility')}>
                            <option value="private">Private (only you)</option>
                            <option value="public">Public (logged-in users)</option>
                        </select>
                    </Field>
                </section>

                <div className={styles.footer}>
                    {formDirty && <span className={ui.hint}>You have unsaved changes to your details.</span>}
                    <button type="button" className="btn contained" onClick={save} disabled={saving || !form.fullName.trim()}>
                        {saving ? <Loader2 size={16} className="spin" aria-hidden="true" /> : <Save size={16} aria-hidden="true" />}
                        {saving ? 'Saving…' : existing ? 'Save changes' : 'Create profile'}
                    </button>
                </div>
            </div>
        )

    const canAdd = isLoggedIn && isCandidate && !loading && !loadError
    return (
        <Page>
            <PageHeader
                icon={UserRound}
                title="Profile"
                subtitle="Keep your details current. This is what matching and employers see."
                actions={
                    canAdd && (
                        <button
                            type="button"
                            className="btn contained"
                            onClick={() => setAddOpen(true)}
                            disabled={!hasProfile || editing !== null}
                            title={hasProfile ? undefined : 'Create your profile first'}
                        >
                            <Plus size={16} aria-hidden="true" /> Add section
                        </button>
                    )
                }
            />
            {body}
            <AddSectionDialog open={addOpen} onClose={() => setAddOpen(false)} onCreate={startAdd} />
            <Dialog
                open={Boolean(toDelete)}
                title="Delete this section?"
                onClose={() => setToDelete(null)}
                actions={
                    <>
                        <button type="button" className="btn outlined" onClick={() => setToDelete(null)}>
                            Cancel
                        </button>
                        <button type="button" className="btn danger" onClick={confirmDelete}>
                            Delete
                        </button>
                    </>
                }
            >
                <p style={{ margin: 0 }}>
                    “{toDelete?.heading}” and everything in it will be removed from your profile. This cannot be undone.
                </p>
            </Dialog>
            <Toast toast={toast} onClose={closeToast} />
        </Page>
    )
}
