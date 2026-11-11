import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Heart, RefreshCw, Search, Sparkles, Upload } from 'lucide-react'
import { api } from '../api'
import { careerPlan, completeness, growthAreas, isSuggested, rankJobs, whyLine, STRONG_ALIGNMENT } from '../careerMatch/matching'
import { loadSaved, storeSaved } from '../careerMatch/savedJobs'
import { deriveSkills } from '../profile/adapters'
import { EMPLOYMENT_TYPES, WORK_MODES, employmentLabel, workModeLabel } from '../format'
import { Link, navigate } from '../router'
import { useSession } from '../session'
import { Dialog, EmptyState, ErrorState, LoginRequired, Page, PageHeader, Pill, SkeletonGrid, Toast } from '../ui'
import styles from './CareerMatch.module.css'

const MAX_RESUME_BYTES = 5 * 1024 * 1024
const RESUME_ACCEPT = '.pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document'
const initials = (name) =>
    (name || '')
        .trim()
        .split(/\s+/)
        .map((p) => p[0])
        .slice(0, 2)
        .join('')
        .toUpperCase() || '—'

function Stat({ label, value, caption }) {
    return (
        <div className={styles.stat}>
            <p className={styles.statLabel}>{label}</p>
            <strong className={styles.statValue}>{value}</strong>
            <span className={styles.statCaption}>{caption}</span>
        </div>
    )
}

function JobCard({ job, saved, onToggleSave, onViewFit }) {
    const hasScore = job.alignment !== null
    return (
        <article className={styles.job}>
            <div className={styles.jobTop}>
                <div className={styles.company}>
                    <div className={styles.logo} aria-hidden="true">
                        {(job.company?.name || '?')[0]}
                    </div>
                    <div>
                        <h3 className={styles.role}>{job.title}</h3>
                        <p className={styles.jobMeta}>
                            {[job.company?.name, job.location, workModeLabel(job.work_mode)].filter(Boolean).join(' · ')}
                        </p>
                        <p className={styles.jobMeta}>{employmentLabel(job.employment_type)}</p>
                    </div>
                </div>
                <span className={`${styles.score} ${hasScore ? '' : styles.scoreNone}`}>
                    {hasScore ? `${job.alignment}% skill alignment*` : 'No required skills listed'}
                </span>
            </div>
            {(job.matched.length > 0 || job.missing.length > 0) && (
                <div className={styles.chips}>
                    {job.matched.map((s) => (
                        <span key={`m-${s}`} className={`${styles.chip} ${styles.chipMatch}`}>
                            ✓ {s}
                        </span>
                    ))}
                    {job.missing.map((s) => (
                        <span key={`g-${s}`} className={`${styles.chip} ${styles.chipGrowth}`}>
                            Growth area: {s}
                        </span>
                    ))}
                </div>
            )}
            <div className={styles.jobBottom}>
                <p className={styles.why}>
                    <strong>Why suggested:</strong> {whyLine(job)}
                </p>
                <div className={styles.jobActions}>
                    <button type="button" className="btn outlined small" onClick={() => onToggleSave(job.id)} aria-pressed={saved}>
                        <Heart size={14} aria-hidden="true" fill={saved ? 'currentColor' : 'none'} />
                        {saved ? 'Saved' : 'Save'}
                    </button>
                    <button type="button" className="btn contained small" onClick={() => onViewFit(job)}>
                        View fit →
                    </button>
                </div>
            </div>
        </article>
    )
}

export default function CareerMatchPage() {
    const { user, isLoggedIn, isCandidate } = useSession()
    const [profile, setProfile] = useState(null)
    const [jobs, setJobs] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)
    const [toast, setToast] = useState(null)

    const [tab, setTab] = useState('all')
    const [input, setInput] = useState('')
    const [q, setQ] = useState('')
    const [employmentType, setEmploymentType] = useState('')
    const [workMode, setWorkMode] = useState('')

    const [saved, setSaved] = useState(() => new Set(loadSaved()))
    const [fit, setFit] = useState(null)
    const [planOpen, setPlanOpen] = useState(false)
    const [uploading, setUploading] = useState(false)
    const fileInput = useRef(null)
    const matchesRef = useRef(null)

    useEffect(() => storeSaved(saved), [saved])

    // Debounce the search box.
    useEffect(() => {
        const t = setTimeout(() => setQ(input.trim()), 300)
        return () => clearTimeout(t)
    }, [input])

    const load = useCallback(async () => {
        setLoading(true)
        setError(null)
        try {
            const [prof, jobsResp] = await Promise.all([
                api('/profiles/me').catch((err) => {
                    if (err.code === 'profile_not_found') return null
                    throw err
                }),
                api('/jobs', { params: { q, employment_type: employmentType, work_mode: workMode, limit: 100 } }),
            ])
            setProfile(prof)
            setJobs(jobsResp.items || [])
        } catch (err) {
            setError(err.message || 'Unable to load your matches. Please try again later.')
        } finally {
            setLoading(false)
        }
    }, [q, employmentType, workMode])

    useEffect(() => {
        if (isLoggedIn && isCandidate) load()
        else setLoading(false)
    }, [isLoggedIn, isCandidate, load])

    const closeToast = useCallback(() => setToast(null), [])

    const skills = useMemo(() => deriveSkills(profile?.sections), [profile])
    // Jobs ranked by alignment against the profile's skills, highest first.
    const ranked = useMemo(() => rankJobs(jobs, skills), [jobs, skills])
    const suggested = useMemo(() => ranked.filter(isSuggested), [ranked])
    const strong = suggested.filter((j) => (j.alignment ?? 0) >= STRONG_ALIGNMENT)
    const complete = useMemo(() => completeness(profile), [profile])
    const growth = useMemo(() => growthAreas(ranked), [ranked])
    const plan = useMemo(() => careerPlan(ranked), [ranked])

    const toggleSave = (id) =>
        setSaved((prev) => {
            const next = new Set(prev)
            if (next.has(id)) next.delete(id)
            else next.add(id)
            return next
        })

    // The visible list: the recommended (suggested) jobs, or the saved ones, under the current filters.
    // Server-side q / type / mode already applied; the saved tab filters the ranked list by id.
    const visible = tab === 'saved' ? ranked.filter((j) => saved.has(j.id)) : suggested
    const savedCount = saved.size

    const refresh = () => {
        load()
        setToast({ severity: 'success', message: 'Recommendations refreshed.' })
    }

    const upload = async (event) => {
        const file = event.target.files?.[0]
        event.target.value = ''
        if (!file) return
        if (file.size > MAX_RESUME_BYTES) {
            setToast({ severity: 'error', message: 'That file is over 5 MB.' })
            return
        }
        setUploading(true)
        try {
            const form = new FormData()
            form.append('file', file)
            await api('/resumes', { method: 'POST', form })
            setToast({ severity: 'success', message: 'Resume uploaded. Review your skills on your profile.' })
        } catch (err) {
            setToast({ severity: 'error', message: err.message || 'Upload failed. Please try again.' })
        } finally {
            setUploading(false)
        }
    }

    const createPlan = () => {
        if (plan.length === 0) {
            setToast({
                severity: 'success',
                message: 'No growth areas across your suggested roles — your skills already cover their requirements.',
            })
            return
        }
        setPlanOpen(true)
    }

    let body
    if (!isLoggedIn) body = <LoginRequired message="Please log in to see your CareerMatch suggestions." />
    else if (!isCandidate) body = <EmptyState>CareerMatch is available to student and candidate accounts.</EmptyState>
    else if (loading) body = <SkeletonGrid count={3} height={180} />
    else if (error) body = <ErrorState message={error} onRetry={load} />
    else
        body = (
            <>
                <section className={styles.hero}>
                    <p className={styles.eyebrow}>YOUR AI CAREER COPILOT</p>
                    <h2 className={styles.heroTitle}>Find the right role. Build the skills to get there.</h2>
                    <p className={styles.heroText}>
                        Explore personalized opportunities, understand qualification gaps, and prepare for your next career step.
                    </p>
                    <button
                        type="button"
                        className="btn contained"
                        onClick={() => matchesRef.current?.scrollIntoView({ behavior: 'smooth' })}
                    >
                        Explore matches →
                    </button>
                </section>

                <div className={styles.stats}>
                    <Stat label="Suggested opportunities" value={suggested.length} caption="Based on your profile" />
                    <Stat label="Strong skill matches" value={strong.length} caption="Across suggested roles" />
                    <Stat
                        label="Profile completeness"
                        value={`${complete.percent}%`}
                        caption={complete.firstMissing ? `Add ${complete.firstMissing} to improve` : 'Your profile is complete'}
                    />
                    <Stat label="Saved opportunities" value={savedCount} caption="Your shortlist" />
                </div>

                <div className={styles.layout}>
                    <section ref={matchesRef}>
                        <div className={styles.panel}>
                            <div className={styles.panelHead}>
                                <div>
                                    <h2 className={styles.panelTitle}>Opportunities for you</h2>
                                    <p className={styles.panelSub}>Transparent skill-based suggestions, not automated hiring decisions.</p>
                                </div>
                                <button type="button" className={styles.linkBtn} onClick={refresh}>
                                    <RefreshCw size={14} aria-hidden="true" /> Refresh
                                </button>
                            </div>

                            <div className={styles.tabs} role="tablist" aria-label="Opportunity lists">
                                <button
                                    type="button"
                                    role="tab"
                                    aria-selected={tab === 'all'}
                                    className={`${styles.tab} ${tab === 'all' ? styles.tabActive : ''}`}
                                    onClick={() => setTab('all')}
                                >
                                    Recommended
                                </button>
                                <button
                                    type="button"
                                    role="tab"
                                    aria-selected={tab === 'saved'}
                                    className={`${styles.tab} ${tab === 'saved' ? styles.tabActive : ''}`}
                                    onClick={() => setTab('saved')}
                                >
                                    Saved jobs
                                </button>
                            </div>

                            <div className={styles.filters}>
                                <div className={styles.searchWrap}>
                                    <Search size={16} aria-hidden="true" />
                                    <input
                                        className={styles.search}
                                        value={input}
                                        onChange={(e) => setInput(e.target.value)}
                                        placeholder="Search roles, companies, skills…"
                                        aria-label="Search roles, companies, skills"
                                    />
                                </div>
                                <select
                                    className={styles.select}
                                    value={employmentType}
                                    onChange={(e) => setEmploymentType(e.target.value)}
                                    aria-label="Employment type"
                                >
                                    <option value="">All types</option>
                                    {EMPLOYMENT_TYPES.map((t) => (
                                        <option key={t.value} value={t.value}>
                                            {t.label}
                                        </option>
                                    ))}
                                </select>
                                <select
                                    className={styles.select}
                                    value={workMode}
                                    onChange={(e) => setWorkMode(e.target.value)}
                                    aria-label="Work mode"
                                >
                                    <option value="">Any location</option>
                                    {WORK_MODES.map((m) => (
                                        <option key={m.value} value={m.value}>
                                            {m.label}
                                        </option>
                                    ))}
                                </select>
                            </div>

                            {visible.length === 0 ? (
                                <p className={styles.empty}>
                                    {tab === 'saved'
                                        ? 'You have not saved any opportunities yet.'
                                        : skills.length === 0
                                          ? 'Add a skills section to your profile to see suggestions matched to you.'
                                          : 'No matching opportunities found.'}
                                </p>
                            ) : (
                                visible.map((job) => (
                                    <JobCard
                                        key={job.id}
                                        job={job}
                                        saved={saved.has(job.id)}
                                        onToggleSave={toggleSave}
                                        onViewFit={setFit}
                                    />
                                ))
                            )}
                            <p className={styles.footnote}>
                                *Skill alignment is the share of a job's required skills found on your profile. It is a suggestion, not a
                                hiring decision.
                            </p>
                        </div>
                    </section>

                    <section>
                        <div className={styles.panel}>
                            <div className={styles.panelHead}>
                                <h2 className={styles.panelTitle}>Your career profile</h2>
                                <Link to="/profile" className={styles.linkBtn}>
                                    Edit
                                </Link>
                            </div>
                            <div className={styles.profileTop}>
                                <div className={styles.avatar} aria-hidden="true">
                                    {initials(profile?.personal?.fullName || user.email)}
                                </div>
                                <div>
                                    <p className={styles.name}>{profile?.personal?.fullName || user.email}</p>
                                    <p className={styles.jobMeta}>
                                        {[profile?.career?.headline, profile?.personal?.location].filter(Boolean).join(' · ') ||
                                            'Add a headline on your profile'}
                                    </p>
                                </div>
                            </div>
                            <div className={styles.barRow}>
                                <span>Profile completeness</span>
                                <strong>{complete.percent}%</strong>
                            </div>
                            <div className={styles.barBg}>
                                <div className={styles.barFill} style={{ width: `${complete.percent}%` }} />
                            </div>
                            <span className={styles.sectionLabel}>Skills identified</span>
                            {skills.length > 0 ? (
                                <ul className={styles.skillChips}>
                                    {skills.map((s) => (
                                        <li key={s}>
                                            <Pill>{s}</Pill>
                                        </li>
                                    ))}
                                </ul>
                            ) : (
                                <p className={styles.uploadHint}>Add a skills section to your profile so matching can use it.</p>
                            )}
                            <div className={styles.upload}>
                                <Upload size={22} className={styles.uploadIcon} aria-hidden="true" />
                                <div>
                                    <input ref={fileInput} type="file" accept={RESUME_ACCEPT} onChange={upload} hidden />
                                    <button
                                        type="button"
                                        className={styles.uploadBtn}
                                        onClick={() => fileInput.current?.click()}
                                        disabled={uploading}
                                    >
                                        {uploading ? 'Uploading…' : 'Upload your resume'}
                                    </button>
                                </div>
                                <p className={styles.uploadHint}>PDF or DOCX · Review extracted skills</p>
                            </div>
                        </div>

                        <div className={styles.panel}>
                            <div className={styles.panelHead}>
                                <h2 className={styles.panelTitle}>AI screening assistant</h2>
                                <span className={styles.advisory}>● Advisory</span>
                            </div>
                            {[
                                ['Parse candidate profile', 'Extract skills, education, projects, experience'],
                                ['Compare job requirements', 'Explain matching and missing qualifications'],
                                ['Recommend development plan', 'Suggest courses, projects and interview prep'],
                                ['Candidate-controlled applications', 'Students apply; employers make hiring decisions'],
                            ].map(([title, text], i) => (
                                <div key={title} className={styles.step}>
                                    <span className={styles.stepNo} aria-hidden="true">
                                        {i + 1}
                                    </span>
                                    <div>
                                        <span className={styles.stepTitle}>{title}</span>
                                        <span className={styles.stepText}>{text}</span>
                                    </div>
                                </div>
                            ))}
                            <button type="button" className="btn contained" style={{ width: '100%' }} onClick={createPlan}>
                                <Sparkles size={16} aria-hidden="true" /> Create my career plan
                            </button>
                        </div>
                    </section>
                </div>
            </>
        )

    return (
        <Page>
            <PageHeader
                icon={Sparkles}
                title="Your next opportunity starts here"
                subtitle="Discover roles that align with your skills, projects, and career goals."
                actions={
                    isLoggedIn &&
                    isCandidate && (
                        <button type="button" className="btn outlined" onClick={() => navigate('/resumes')}>
                            <Upload size={16} aria-hidden="true" /> Update resume
                        </button>
                    )
                }
            />
            {body}

            <Dialog
                open={Boolean(fit)}
                title={fit ? `${fit.title} — ${fit.company?.name || ''}` : ''}
                onClose={() => setFit(null)}
                actions={
                    <>
                        <button type="button" className="btn outlined" onClick={() => setFit(null)}>
                            Close
                        </button>
                        {fit && (
                            <Link to={`/jobs/${fit.id}`} className="btn contained">
                                View job
                            </Link>
                        )}
                    </>
                }
            >
                {fit && (
                    <div>
                        <p style={{ marginTop: 0 }}>
                            <strong>Skill alignment:</strong> {fit.alignment === null ? 'No required skills listed' : `${fit.alignment}%`}
                        </p>
                        <p>
                            <strong>Matching skills:</strong> {fit.matched.length ? fit.matched.join(', ') : 'None yet'}
                        </p>
                        <p>
                            <strong>Development areas:</strong> {fit.missing.length ? fit.missing.join(', ') : 'None'}
                        </p>
                        <p>
                            <strong>Why suggested:</strong> {whyLine(fit)}
                        </p>
                        <p className={styles.footnote}>
                            Full job description and your application are on the job page. No automated hiring decision is made.
                        </p>
                    </div>
                )}
            </Dialog>

            <Dialog
                open={planOpen}
                title="Your suggested career plan"
                onClose={() => setPlanOpen(false)}
                actions={
                    <button type="button" className="btn contained" onClick={() => setPlanOpen(false)}>
                        Got it
                    </button>
                }
            >
                <p style={{ marginTop: 0 }}>Based on the growth areas across your suggested roles ({growth.slice(0, 3).join(', ')}):</p>
                <ul className={styles.dialogList}>
                    {plan.map((step) => (
                        <li key={step}>{step}</li>
                    ))}
                </ul>
            </Dialog>

            <Toast toast={toast} onClose={closeToast} />
        </Page>
    )
}
