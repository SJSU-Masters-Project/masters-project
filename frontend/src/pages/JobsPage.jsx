import React, { useCallback, useEffect, useState } from 'react'
import { BriefcaseBusiness, MapPin, Search, SearchX } from 'lucide-react'
import { api } from '../api'
import { EMPLOYMENT_TYPES, WORK_MODES, employmentLabel, workModeLabel } from '../format'
import { Link } from '../router'
import { EmptyState, ErrorState, Page, PageHeader, Pill, SkeletonGrid, cx } from '../ui'
import ui from '../ui.module.css'
import styles from './Jobs.module.css'

const PAGE_SIZE = 12

export function JobCard({ job }) {
    const shown = job.skills.slice(0, 4)
    return (
        <Link to={`/jobs/${job.id}`} className={cx(ui.card, ui.cardLink)}>
            <h2 className={styles.jobTitle}>{job.title}</h2>
            <p className={styles.company}>{job.company.name}</p>
            <p className={styles.meta}>
                <MapPin size={14} aria-hidden="true" /> {job.location || 'Location not specified'}
            </p>
            <div className={styles.pills}>
                <Pill>{employmentLabel(job.employment_type)}</Pill>
                <Pill tone="muted">{workModeLabel(job.work_mode)}</Pill>
                {job.openings > 1 && <Pill tone="muted">{job.openings} openings</Pill>}
            </div>
            {shown.length > 0 && (
                <div className={styles.skills}>
                    {shown.map((s) => (
                        <span key={s.name} className={s.required ? styles.skillReq : styles.skill}>
                            {s.name}
                        </span>
                    ))}
                    {job.skills.length > shown.length && <span className={styles.skill}>+{job.skills.length - shown.length}</span>}
                </div>
            )}
        </Link>
    )
}

export default function JobsPage() {
    const [input, setInput] = useState('')
    const [q, setQ] = useState('')
    const [workMode, setWorkMode] = useState('')
    const [employmentType, setEmploymentType] = useState('')
    const [offset, setOffset] = useState(0)
    const [data, setData] = useState(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    // Debounce the search box so each keystroke does not hit the API.
    useEffect(() => {
        const t = setTimeout(() => {
            setQ(input.trim())
            setOffset(0)
        }, 300)
        return () => clearTimeout(t)
    }, [input])

    const load = useCallback(async () => {
        setLoading(true)
        setError(null)
        try {
            setData(await api('/jobs', { params: { q, work_mode: workMode, employment_type: employmentType, limit: PAGE_SIZE, offset } }))
        } catch (err) {
            setError(err.message || 'Unable to load jobs. Please try again later.')
        } finally {
            setLoading(false)
        }
    }, [q, workMode, employmentType, offset])

    useEffect(() => {
        load()
    }, [load])

    const filtered = Boolean(q || workMode || employmentType)
    const total = data?.total || 0
    const items = data?.items || []

    return (
        <Page>
            <PageHeader
                icon={BriefcaseBusiness}
                title="Jobs"
                subtitle="Browse open roles from companies hiring through myAcademic Careers."
            />

            <div className={styles.filters}>
                <div className={styles.searchWrap}>
                    <Search size={16} aria-hidden="true" />
                    <input
                        className={styles.search}
                        type="search"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder="Search by title, company or keyword"
                        aria-label="Search jobs"
                    />
                </div>
                <select
                    className={ui.select}
                    value={workMode}
                    onChange={(e) => {
                        setWorkMode(e.target.value)
                        setOffset(0)
                    }}
                    aria-label="Work mode"
                >
                    <option value="">Any work mode</option>
                    {WORK_MODES.map((m) => (
                        <option key={m.value} value={m.value}>
                            {m.label}
                        </option>
                    ))}
                </select>
                <select
                    className={ui.select}
                    value={employmentType}
                    onChange={(e) => {
                        setEmploymentType(e.target.value)
                        setOffset(0)
                    }}
                    aria-label="Employment type"
                >
                    <option value="">Any type</option>
                    {EMPLOYMENT_TYPES.map((m) => (
                        <option key={m.value} value={m.value}>
                            {m.label}
                        </option>
                    ))}
                </select>
            </div>

            {loading && <SkeletonGrid />}
            {!loading && error && <ErrorState message={error} onRetry={load} />}
            {!loading && !error && items.length === 0 && (
                <EmptyState icon={SearchX}>
                    {filtered ? 'No jobs match your search. Try different filters.' : 'No open jobs yet. Check back soon.'}
                </EmptyState>
            )}
            {!loading && !error && items.length > 0 && (
                <>
                    <div className={ui.grid}>
                        {items.map((job) => (
                            <JobCard key={job.id} job={job} />
                        ))}
                    </div>
                    <div className={styles.pager}>
                        <span className={ui.hint}>
                            {offset + 1}–{Math.min(offset + PAGE_SIZE, total)} of {total}
                        </span>
                        <button
                            type="button"
                            className="btn outlined"
                            disabled={offset === 0}
                            onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
                        >
                            Previous
                        </button>
                        <button
                            type="button"
                            className="btn outlined"
                            disabled={offset + PAGE_SIZE >= total}
                            onClick={() => setOffset(offset + PAGE_SIZE)}
                        >
                            Next
                        </button>
                    </div>
                </>
            )}
        </Page>
    )
}
