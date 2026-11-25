import React, { useCallback, useEffect, useRef, useState } from 'react'
import { Download, FileText, Loader2, Trash2, Upload } from 'lucide-react'
import { api, downloadFile } from '../api'
import { formatBytes, formatDate } from '../format'
import { useSession } from '../session'
import { Dialog, EmptyState, ErrorState, LoginRequired, Page, PageHeader, Pill, SkeletonGrid, Toast, cx } from '../ui'
import ui from '../ui.module.css'
import styles from './Resumes.module.css'

const MAX_BYTES = 5 * 1024 * 1024
const ACCEPT = '.pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document'

const TEXT_STATUS = {
    done: { label: 'Text extracted', tone: 'success' },
    pending: { label: 'Processing', tone: 'muted' },
    empty: { label: 'No text found', tone: 'warning' },
    failed: { label: 'Extraction failed', tone: 'error' },
}

export default function ResumesPage() {
    const { isLoggedIn, isCandidate } = useSession()
    const [items, setItems] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)
    const [uploading, setUploading] = useState(false)
    const [toDelete, setToDelete] = useState(null)
    const [deleting, setDeleting] = useState(false)
    const [toast, setToast] = useState(null)
    const fileInput = useRef(null)

    const load = useCallback(async () => {
        setLoading(true)
        setError(null)
        try {
            setItems((await api('/resumes', { params: { limit: 100 } })).items)
        } catch (err) {
            setError(err.message || 'Unable to load your resumes. Please try again later.')
        } finally {
            setLoading(false)
        }
    }, [])

    useEffect(() => {
        if (isLoggedIn && isCandidate) load()
        else setLoading(false)
    }, [isLoggedIn, isCandidate, load])

    const closeToast = useCallback(() => setToast(null), [])

    const upload = async (event) => {
        const file = event.target.files?.[0]
        event.target.value = ''
        if (!file) return
        if (file.size > MAX_BYTES) {
            setToast({ severity: 'error', message: 'That file is over 5 MB.' })
            return
        }
        setUploading(true)
        try {
            const form = new FormData()
            form.append('file', file)
            await api('/resumes', { method: 'POST', form })
            setToast({ severity: 'success', message: 'Resume uploaded.' })
            await load()
        } catch (err) {
            setToast({ severity: 'error', message: err.message || 'Upload failed. Please try again.' })
        } finally {
            setUploading(false)
        }
    }

    const confirmDelete = async () => {
        setDeleting(true)
        try {
            await api(`/resumes/${toDelete.id}`, { method: 'DELETE' })
            setItems((cur) => cur.filter((r) => r.id !== toDelete.id))
            setToast({ severity: 'success', message: 'Resume deleted.' })
            setToDelete(null)
        } catch (err) {
            setToast({ severity: 'error', message: err.message || 'Could not delete the resume.' })
        } finally {
            setDeleting(false)
        }
    }

    const download = async (resume) => {
        try {
            await downloadFile(`/resumes/${resume.id}/download`, resume.filename)
        } catch (err) {
            setToast({ severity: 'error', message: err.message || 'Download failed.' })
        }
    }

    const uploadButton = (
        <>
            <input ref={fileInput} type="file" accept={ACCEPT} onChange={upload} hidden />
            <button type="button" className="btn contained" disabled={uploading} onClick={() => fileInput.current?.click()}>
                {uploading ? <Loader2 size={16} className="spin" aria-hidden="true" /> : <Upload size={16} aria-hidden="true" />}
                {uploading ? 'Uploading…' : 'Upload resume'}
            </button>
        </>
    )

    let body
    if (!isLoggedIn) body = <LoginRequired message="Please log in to manage your resumes." />
    else if (!isCandidate) body = <EmptyState>Resumes are available to student and candidate accounts.</EmptyState>
    else if (loading) body = <SkeletonGrid count={3} height={110} />
    else if (error) body = <ErrorState message={error} onRetry={load} />
    else if (items.length === 0)
        body = <EmptyState icon={FileText}>You have not uploaded a resume yet. PDF or DOCX, up to 5 MB.</EmptyState>
    else
        body = (
            <ul className={styles.list}>
                {items.map((r) => {
                    const status = TEXT_STATUS[r.text_status] || { label: r.text_status, tone: 'muted' }
                    return (
                        <li key={r.id} className={cx(ui.card, styles.row)}>
                            <FileText className={ui.titleIcon} size={28} aria-hidden="true" />
                            <div className={styles.info}>
                                <strong className={styles.name}>{r.filename}</strong>
                                <span className={ui.hint}>
                                    {formatBytes(r.size_bytes)} · uploaded {formatDate(r.created_at)}
                                </span>
                            </div>
                            <Pill tone={status.tone}>{status.label}</Pill>
                            <div className={styles.actions}>
                                <button
                                    type="button"
                                    className="btn outlined small"
                                    onClick={() => download(r)}
                                    aria-label={`Download ${r.filename}`}
                                >
                                    <Download size={14} aria-hidden="true" /> Download
                                </button>
                                <button
                                    type="button"
                                    className="btn danger small"
                                    onClick={() => setToDelete(r)}
                                    aria-label={`Delete ${r.filename}`}
                                >
                                    <Trash2 size={14} aria-hidden="true" /> Delete
                                </button>
                            </div>
                        </li>
                    )
                })}
            </ul>
        )

    return (
        <Page>
            <PageHeader
                icon={FileText}
                title="Resumes"
                subtitle="Upload up to 10 resumes. Link one to your profile so employers and matching can use it."
                actions={isLoggedIn && isCandidate ? uploadButton : null}
            />
            {body}
            <Dialog
                open={Boolean(toDelete)}
                title="Delete resume?"
                onClose={() => !deleting && setToDelete(null)}
                maxWidth={460}
                actions={
                    <>
                        <button type="button" className="btn outlined" disabled={deleting} onClick={() => setToDelete(null)}>
                            Cancel
                        </button>
                        <button type="button" className="btn contained" disabled={deleting} onClick={confirmDelete}>
                            {deleting ? 'Deleting…' : 'Delete'}
                        </button>
                    </>
                }
            >
                <p style={{ margin: 0 }}>
                    <strong>{toDelete?.filename}</strong> will be removed. If it is linked to your profile, the link is cleared.
                </p>
            </Dialog>
            <Toast toast={toast} onClose={closeToast} />
        </Page>
    )
}
