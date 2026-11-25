import React, { useCallback, useEffect, useState } from 'react'
import { Building2, ExternalLink, Pencil, Plus } from 'lucide-react'
import { api } from '../api'
import { employmentLabel, formatDate, workModeLabel } from '../format'
import { Link } from '../router'
import { useSession } from '../session'
import { EmptyState, ErrorState, LoginRequired, Page, PageHeader, Pill, SkeletonGrid, Toast, cx } from '../ui'
import ui from '../ui.module.css'
import { CompanyForm, JobFormDialog } from './EmployerForms'
import styles from './Employer.module.css'

const STATUS_TONE = { draft: 'muted', open: 'success', closed: 'warning' }

export default function EmployerPage() {
    const { isLoggedIn, isEmployer } = useSession()
    const [company, setCompany] = useState(null)
    const [jobs, setJobs] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)
    const [editingCompany, setEditingCompany] = useState(false)
    const [jobDialog, setJobDialog] = useState(null) // { job } when open; job is null for a new one
    const [busyId, setBusyId] = useState(null)
    const [toast, setToast] = useState(null)

    const load = useCallback(async () => {
        setLoading(true)
        setError(null)
        try {
            let mine = null
            try {
                mine = await api('/companies/mine')
            } catch (err) {
                if (err.code !== 'no_company') throw err
            }
            setCompany(mine)
            setJobs(mine ? (await api(`/companies/${mine.id}/jobs`, { params: { limit: 100 } })).items : [])
        } catch (err) {
            setError(err.message || 'Unable to load your company. Please try again later.')
        } finally {
            setLoading(false)
        }
    }, [])

    useEffect(() => {
        if (isLoggedIn && isEmployer) load()
        else setLoading(false)
    }, [isLoggedIn, isEmployer, load])

    const closeToast = useCallback(() => setToast(null), [])
    const notify = (severity, message) => setToast({ severity, message })

    const transition = async (job, action) => {
        setBusyId(job.id)
        try {
            const updated = await api(`/jobs/${job.id}/${action}`, { method: 'POST' })
            setJobs((cur) => cur.map((j) => (j.id === updated.id ? updated : j)))
            notify('success', action === 'publish' ? 'Job published.' : 'Job closed.')
        } catch (err) {
            notify('error', err.message || 'That did not work. Please try again.')
        } finally {
            setBusyId(null)
        }
    }

    const onJobSaved = (saved) => {
        setJobs((cur) => (cur.some((j) => j.id === saved.id) ? cur.map((j) => (j.id === saved.id ? saved : j)) : [saved, ...cur]))
        setJobDialog(null)
        notify('success', 'Job saved.')
    }

    let body
    if (!isLoggedIn) body = <LoginRequired message="Please log in to manage your company and jobs." />
    else if (!isEmployer) body = <EmptyState>This area is for employer accounts.</EmptyState>
    else if (loading) body = <SkeletonGrid count={2} height={160} />
    else if (error) body = <ErrorState message={error} onRetry={load} />
    else if (!company || editingCompany)
        body = (
            <div className={cx(ui.card, styles.companyForm)}>
                <h2 className={ui.sectionTitle}>{company ? 'Edit company' : 'Set up your company'}</h2>
                {!company && (
                    <p className={ui.hint} style={{ marginTop: '-0.5rem', marginBottom: '1rem' }}>
                        Create your company before posting jobs.
                    </p>
                )}
                <CompanyForm
                    company={company}
                    onCancel={company ? () => setEditingCompany(false) : null}
                    onSaved={(saved) => {
                        setCompany(saved)
                        setEditingCompany(false)
                        notify('success', 'Company saved.')
                    }}
                />
            </div>
        )
    else
        body = (
            <>
                <section className={cx(ui.card, styles.company)}>
                    <div>
                        <h2 className={styles.companyName}>{company.name}</h2>
                        {company.location && <p className={ui.hint}>{company.location}</p>}
                        {company.description && <p className={styles.companyDesc}>{company.description}</p>}
                        {company.website && (
                            <a href={company.website} target="_blank" rel="noopener noreferrer" className={styles.site}>
                                {company.website} <ExternalLink size={13} aria-hidden="true" />
                            </a>
                        )}
                    </div>
                    <button type="button" className="btn outlined" onClick={() => setEditingCompany(true)}>
                        <Pencil size={14} aria-hidden="true" /> Edit
                    </button>
                </section>

                <div className={styles.jobsHeader}>
                    <h2 className={ui.sectionTitle} style={{ margin: 0 }}>
                        Your jobs
                    </h2>
                    <button type="button" className="btn contained" onClick={() => setJobDialog({ job: null })}>
                        <Plus size={16} aria-hidden="true" /> Post a job
                    </button>
                </div>

                {jobs.length === 0 ? (
                    <EmptyState>No jobs yet. Create a draft, then publish it when it is ready.</EmptyState>
                ) : (
                    <ul className={styles.jobList}>
                        {jobs.map((job) => (
                            <li key={job.id} className={cx(ui.card, styles.jobRow)}>
                                <div className={styles.jobInfo}>
                                    <div className={styles.jobTitleLine}>
                                        <Link to={`/jobs/${job.id}`} className={styles.jobLink}>
                                            {job.title}
                                        </Link>
                                        <Pill tone={STATUS_TONE[job.status]}>{job.status}</Pill>
                                    </div>
                                    <span className={ui.hint}>
                                        {employmentLabel(job.employment_type)} · {workModeLabel(job.work_mode)} · {job.openings}{' '}
                                        {job.openings === 1 ? 'opening' : 'openings'} · updated {formatDate(job.updated_at)}
                                    </span>
                                </div>
                                <div className={styles.jobActions}>
                                    {job.status !== 'closed' && (
                                        <button type="button" className="btn outlined small" onClick={() => setJobDialog({ job })}>
                                            Edit
                                        </button>
                                    )}
                                    {job.status === 'draft' && (
                                        <button
                                            type="button"
                                            className="btn contained small"
                                            disabled={busyId === job.id}
                                            onClick={() => transition(job, 'publish')}
                                        >
                                            Publish
                                        </button>
                                    )}
                                    {job.status === 'open' && (
                                        <button
                                            type="button"
                                            className="btn danger small"
                                            disabled={busyId === job.id}
                                            onClick={() => transition(job, 'close')}
                                        >
                                            Close
                                        </button>
                                    )}
                                </div>
                            </li>
                        ))}
                    </ul>
                )}
            </>
        )

    return (
        <Page>
            <PageHeader icon={Building2} title="Company" subtitle="Manage your company profile and the jobs you post." />
            {body}
            <JobFormDialog open={Boolean(jobDialog)} job={jobDialog?.job} onClose={() => setJobDialog(null)} onSaved={onJobSaved} />
            <Toast toast={toast} onClose={closeToast} />
        </Page>
    )
}
