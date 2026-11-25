import React, { useCallback, useEffect, useState } from 'react'
import { ArrowLeft, MapPin, SearchX } from 'lucide-react'
import { api } from '../api'
import { employmentLabel, formatDate, workModeLabel } from '../format'
import { Link } from '../router'
import { EmptyState, ErrorState, Page, Pill, SkeletonGrid } from '../ui'
import ui from '../ui.module.css'
import styles from './Jobs.module.css'

export default function JobDetailPage({ id }) {
    const [job, setJob] = useState(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)
    const [notFound, setNotFound] = useState(false)

    const load = useCallback(async () => {
        setLoading(true)
        setError(null)
        setNotFound(false)
        try {
            setJob(await api(`/jobs/${encodeURIComponent(id)}`))
        } catch (err) {
            if (err.status === 404 || err.status === 400) setNotFound(true)
            else setError(err.message || 'Unable to load this job. Please try again later.')
        } finally {
            setLoading(false)
        }
    }, [id])

    useEffect(() => {
        load()
    }, [load])

    const back = (
        <Link to="/jobs" className={styles.back}>
            <ArrowLeft size={16} aria-hidden="true" /> All jobs
        </Link>
    )

    return (
        <Page>
            {back}
            {loading && <SkeletonGrid count={1} height={320} />}
            {!loading && error && <ErrorState message={error} onRetry={load} />}
            {!loading && notFound && (
                <EmptyState
                    icon={SearchX}
                    action={
                        <Link to="/jobs" className="btn outlined">
                            Browse jobs
                        </Link>
                    }
                >
                    This job is not available. It may have been closed or removed.
                </EmptyState>
            )}
            {!loading && job && (
                <article className={ui.card}>
                    <h1 className={styles.detailTitle}>{job.title}</h1>
                    <p className={styles.company}>{job.company.name}</p>
                    <p className={styles.meta}>
                        <MapPin size={14} aria-hidden="true" /> {job.location || 'Location not specified'}
                    </p>
                    <div className={styles.pills}>
                        <Pill>{employmentLabel(job.employment_type)}</Pill>
                        <Pill tone="muted">{workModeLabel(job.work_mode)}</Pill>
                        <Pill tone="muted">
                            {job.openings} {job.openings === 1 ? 'opening' : 'openings'}
                        </Pill>
                        {job.status !== 'open' && <Pill tone="warning">{job.status}</Pill>}
                    </div>

                    <h2 className={ui.sectionTitle} style={{ marginTop: '1.5rem' }}>
                        Skills
                    </h2>
                    <div className={styles.skills} style={{ marginTop: 0 }}>
                        {job.skills.map((s) => (
                            <span key={s.name} className={s.required ? styles.skillReq : styles.skill}>
                                {s.name} · {s.required ? 'required' : 'optional'}
                            </span>
                        ))}
                    </div>

                    <h2 className={ui.sectionTitle} style={{ marginTop: '1.5rem' }}>
                        About the role
                    </h2>
                    <p className={styles.description}>{job.description}</p>
                    {job.published_at && <p className={ui.hint}>Posted {formatDate(job.published_at)}</p>}
                </article>
            )}
        </Page>
    )
}
