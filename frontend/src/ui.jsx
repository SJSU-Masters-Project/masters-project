import React, { useEffect, useRef } from 'react'
import { AlertCircle, CheckCircle2, Inbox, X } from 'lucide-react'
import { Link } from './router'
import styles from './ui.module.css'

export const cx = (...names) => names.filter(Boolean).join(' ')

export function PageHeader({ icon: Icon, title, subtitle, actions }) {
    return (
        <header className={styles.header}>
            <div>
                <h1 className={styles.title}>
                    {Icon && <Icon className={styles.titleIcon} size={30} aria-hidden="true" />} {title}
                </h1>
                {subtitle && <p className={styles.subtitle}>{subtitle}</p>}
            </div>
            {actions}
        </header>
    )
}

export function Page({ children }) {
    return <div className={styles.container}>{children}</div>
}

export function SkeletonGrid({ count = 6, height }) {
    return (
        <div className={styles.grid} aria-busy="true" aria-label="Loading">
            {Array.from({ length: count }, (_, i) => (
                <div key={i} className={styles.skeletonCard} style={height ? { height } : undefined} />
            ))}
        </div>
    )
}

export function EmptyState({ icon: Icon = Inbox, children, action }) {
    return (
        <div className={styles.emptyState}>
            <Icon className={styles.stateIcon} size={32} aria-hidden="true" />
            <p>{children}</p>
            {action}
        </div>
    )
}

export function ErrorState({ message, onRetry }) {
    return (
        <div className={cx(styles.emptyState, styles.errorState)} role="alert">
            <AlertCircle className={styles.stateIcon} size={32} aria-hidden="true" />
            <p>{message}</p>
            {onRetry && (
                <button type="button" className="btn outlined" onClick={onRetry}>
                    Retry
                </button>
            )}
        </div>
    )
}

export function LoginRequired({ message }) {
    return (
        <EmptyState
            action={
                <Link to="/login" className="btn contained">
                    Log in
                </Link>
            }
        >
            {message}
        </EmptyState>
    )
}

export function Pill({ tone, children }) {
    const toneClass = { muted: styles.pillMuted, success: styles.pillSuccess, warning: styles.pillWarning, error: styles.pillError }[tone]
    return <span className={cx(styles.pill, toneClass)}>{children}</span>
}

export function Field({ label, htmlFor, hint, error, children }) {
    return (
        <div className={styles.field}>
            <label className={styles.label} htmlFor={htmlFor}>
                {label}
            </label>
            {children}
            {error ? <span className={styles.fieldError}>{error}</span> : hint && <span className={styles.hint}>{hint}</span>}
        </div>
    )
}

export function FormError({ message, lines }) {
    if (!message) return null
    return (
        <div className={styles.formError} role="alert">
            <AlertCircle size={16} aria-hidden="true" style={{ flex: 'none', marginTop: 2 }} />
            <div>
                {message}
                {lines?.length > 0 && (
                    <ul style={{ margin: '0.25rem 0 0', paddingLeft: '1.1rem' }}>
                        {lines.map((l) => (
                            <li key={l}>{l}</li>
                        ))}
                    </ul>
                )}
            </div>
        </div>
    )
}

export function Dialog({ open, title, onClose, children, actions, maxWidth }) {
    const ref = useRef(null)
    useEffect(() => {
        if (!open) return undefined
        const onKey = (e) => e.key === 'Escape' && onClose()
        document.addEventListener('keydown', onKey)
        ref.current?.focus()
        return () => document.removeEventListener('keydown', onKey)
    }, [open, onClose])
    if (!open) return null
    return (
        <div className={styles.backdrop} onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
            <div
                className={styles.dialog}
                role="dialog"
                aria-modal="true"
                aria-label={title}
                ref={ref}
                tabIndex={-1}
                style={maxWidth ? { maxWidth } : undefined}
            >
                <h2 className={styles.dialogTitle}>{title}</h2>
                <div className={styles.dialogBody}>{children}</div>
                <div className={styles.dialogActions}>{actions}</div>
            </div>
        </div>
    )
}

// Toast that closes itself after 6s (handoff 10.2). `toast` is { severity, message } or null.
export function Toast({ toast, onClose }) {
    useEffect(() => {
        if (!toast) return undefined
        const t = setTimeout(onClose, 6000)
        return () => clearTimeout(t)
    }, [toast, onClose])
    if (!toast) return null
    const Icon = toast.severity === 'error' ? AlertCircle : CheckCircle2
    return (
        <div className={cx(styles.toast, toast.severity === 'error' ? styles.toastError : styles.toastSuccess)} role="status">
            <Icon size={18} aria-hidden="true" />
            <span>{toast.message}</span>
            <button type="button" onClick={onClose} aria-label="Dismiss">
                <X size={16} />
            </button>
        </div>
    )
}
