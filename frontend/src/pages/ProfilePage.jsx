import React, { useCallback, useEffect, useState } from 'react'
import { Loader2, Save, UserRound } from 'lucide-react'
import { api } from '../api'
import { EMPLOYMENT_TYPES, WORK_MODES, detailLines, splitList } from '../format'
import { useSession } from '../session'
import { EmptyState, ErrorState, Field, FormError, LoginRequired, Page, PageHeader, SkeletonGrid, Toast, cx } from '../ui'
import ui from '../ui.module.css'
import styles from './Profile.module.css'

const blank = {
    fullName: '',
    phone: '',
    location: '',
    headline: '',
    summary: '',
    skills: '',
    resumeId: '',
    targetRoles: '',
    employmentTypes: [],
    workModes: [],
    preferredLocations: '',
    willingToRelocate: false,
    visibility: 'private',
}

// Profile document -> editable form values.
function toForm(profile) {
    const p = profile.personal || {}
    const c = profile.career || {}
    const j = profile.jobPreferences || {}
    return {
        fullName: p.fullName || '',
        phone: p.phone || '',
        location: p.location || '',
        headline: c.headline || '',
        summary: c.summary || '',
        skills: (c.skills || []).join(', '),
        resumeId: c.resumeId || '',
        targetRoles: (j.targetRoles || []).join(', '),
        employmentTypes: j.employmentTypes || [],
        workModes: j.workModes || [],
        preferredLocations: (j.preferredLocations || []).join(', '),
        willingToRelocate: Boolean(j.willingToRelocate),
        visibility: profile.visibility || 'private',
    }
}

const drop = (obj) => Object.fromEntries(Object.entries(obj).filter(([, v]) => v !== '' && v !== undefined))

// Form values -> request body. Fields the form does not edit (experience, projects,
// availableFrom, ...) are carried over from the saved profile so they are not lost.
function toBody(form, email, existing) {
    const personal = { ...(existing?.personal || {}), email: existing?.personal?.email || email, fullName: form.fullName.trim() }
    personal.phone = form.phone.trim()
    personal.location = form.location.trim()
    const career = {
        ...(existing?.career || {}),
        headline: form.headline.trim(),
        summary: form.summary.trim(),
        skills: splitList(form.skills),
        resumeId: form.resumeId,
    }
    const prefs = {
        ...(existing?.jobPreferences || {}),
        targetRoles: splitList(form.targetRoles),
        employmentTypes: form.employmentTypes,
        workModes: form.workModes,
        preferredLocations: splitList(form.preferredLocations),
        willingToRelocate: form.willingToRelocate,
    }
    if (prefs.preferredLocations.length === 0) delete prefs.preferredLocations
    return { visibility: form.visibility, personal: drop(personal), career: drop(career), jobPreferences: prefs }
}

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

export default function ProfilePage() {
    const { user, isLoggedIn, isCandidate } = useSession()
    const [existing, setExisting] = useState(null)
    const [resumes, setResumes] = useState([])
    const [form, setForm] = useState(blank)
    const [loading, setLoading] = useState(true)
    const [loadError, setLoadError] = useState(null)
    const [saving, setSaving] = useState(false)
    const [saveError, setSaveError] = useState(null)
    const [toast, setToast] = useState(null)

    const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.type === 'checkbox' ? e.target.checked : e.target.value }))

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
            setExisting(profile)
            setResumes(list.items)
            setForm(profile ? toForm(profile) : blank)
        } catch (err) {
            setLoadError(err.message || 'Unable to load your profile. Please try again later.')
        } finally {
            setLoading(false)
        }
    }, [])

    useEffect(() => {
        if (isLoggedIn && isCandidate) load()
        else setLoading(false)
    }, [isLoggedIn, isCandidate, load])

    const closeToast = useCallback(() => setToast(null), [])

    const save = async (event) => {
        event.preventDefault()
        if (saving) return
        setSaving(true)
        setSaveError(null)
        try {
            const body = toBody(form, user.email, existing)
            const saved = await api('/profiles/me', { method: existing ? 'PATCH' : 'PUT', body })
            setExisting(saved)
            setForm(toForm(saved))
            setToast({ severity: 'success', message: 'Profile saved.' })
        } catch (err) {
            setSaveError({ message: err.message || 'Could not save your profile.', lines: detailLines(err.details) })
        } finally {
            setSaving(false)
        }
    }

    let body
    if (!isLoggedIn) body = <LoginRequired message="Please log in to edit your profile." />
    else if (!isCandidate) body = <EmptyState>Profiles are available to student and candidate accounts.</EmptyState>
    else if (loading) body = <SkeletonGrid count={2} height={260} />
    else if (loadError) body = <ErrorState message={loadError} onRetry={load} />
    else
        body = (
            <form onSubmit={save} className={styles.form} noValidate>
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
                    <Field label="Skills" htmlFor="pf-skills" hint="Separate with commas.">
                        <input
                            id="pf-skills"
                            className={ui.input}
                            value={form.skills}
                            onChange={set('skills')}
                            placeholder="Python, React, SQL"
                        />
                    </Field>
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
                    <button type="submit" className="btn contained" disabled={saving || !form.fullName.trim()}>
                        {saving ? <Loader2 size={16} className="spin" aria-hidden="true" /> : <Save size={16} aria-hidden="true" />}
                        {saving ? 'Saving…' : existing ? 'Save changes' : 'Create profile'}
                    </button>
                </div>
            </form>
        )

    return (
        <Page>
            <PageHeader icon={UserRound} title="Profile" subtitle="Keep your details current. This is what matching and employers see." />
            {body}
            <Toast toast={toast} onClose={closeToast} />
        </Page>
    )
}
