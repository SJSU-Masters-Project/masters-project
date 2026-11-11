import React, { useCallback, useEffect, useState } from 'react'
import { BriefcaseBusiness, Building2, CalendarDays, FileText, LogIn, LogOut, Moon, Sun, UserRound } from 'lucide-react'
import { Link } from './router'
import { useSession } from './session'
import './shell.css'

const THEME_KEY = 'careers.theme'

function initialTheme() {
    try {
        const saved = localStorage.getItem(THEME_KEY)
        if (saved === 'light' || saved === 'dark') return saved
    } catch {
        // storage blocked: fall through to the system preference
    }
    return window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

// Applies data-theme to <html> as the platform does (handoff section 4).
export function useTheme() {
    const [theme, setTheme] = useState(initialTheme)
    useEffect(() => {
        document.documentElement.setAttribute('data-theme', theme)
        try {
            localStorage.setItem(THEME_KEY, theme)
        } catch {
            // not persisted; still applies for this page
        }
    }, [theme])
    const toggle = useCallback(() => setTheme((t) => (t === 'dark' ? 'light' : 'dark')), [])
    return [theme, toggle]
}

function navItems({ isCandidate, isEmployer }) {
    const items = [{ to: '/jobs', label: 'Jobs', icon: BriefcaseBusiness, match: (p) => p === '/' || p.startsWith('/jobs') }]
    if (isCandidate) {
        items.push({ to: '/profile', label: 'Profile', icon: UserRound, match: (p) => p.startsWith('/profile') })
        items.push({ to: '/resumes', label: 'Resumes', icon: FileText, match: (p) => p.startsWith('/resumes') })
    }
    if (isEmployer) items.push({ to: '/employer', label: 'Company', icon: Building2, match: (p) => p.startsWith('/employer') })
    return items
}

export default function Shell({ path, theme, toggleTheme, children }) {
    const { user, isLoggedIn, isCandidate, isEmployer, signOut } = useSession()
    const items = navItems({ isCandidate, isEmployer })
    const today = new Date().toLocaleDateString(undefined, { weekday: 'long', month: 'long', day: 'numeric' })

    const links = (
        <>
            {items.map(({ to, label, icon: Icon, match }) => (
                <Link
                    key={to}
                    to={to}
                    className={`shell-item${match(path) ? ' active' : ''}`}
                    aria-current={match(path) ? 'page' : undefined}
                >
                    <Icon size={22} aria-hidden="true" />
                    <span>{label}</span>
                </Link>
            ))}
        </>
    )

    return (
        <div className="shell">
            <aside className="shell-sidebar">
                <Link to="/jobs" className="shell-logo" aria-label="myAcademic Careers home">
                    MA
                </Link>
                <nav className="shell-nav" aria-label="Main navigation">
                    {links}
                </nav>
            </aside>
            <div className="shell-main">
                <header className="shell-header">
                    <Link to="/jobs" className="shell-wordmark">
                        <em>my</em>Academic
                    </Link>
                    <div className="shell-spacer" />
                    <span className="shell-date">
                        <CalendarDays size={14} aria-hidden="true" /> {today}
                    </span>
                    {isLoggedIn && <span className="shell-user">{user.email}</span>}
                    <button
                        type="button"
                        className="shell-icon-btn"
                        onClick={toggleTheme}
                        aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
                    >
                        {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
                    </button>
                    {isLoggedIn ? (
                        <button type="button" className="btn outlined" onClick={signOut}>
                            <LogOut size={16} aria-hidden="true" /> Log out
                        </button>
                    ) : (
                        <Link to="/login" className="btn contained">
                            <LogIn size={16} aria-hidden="true" /> Log in
                        </Link>
                    )}
                </header>
                <main className="shell-content">{children}</main>
                <footer className="shell-footer">
                    <span>myAcademic Careers</span>
                    <span>© 2026 myAcademic</span>
                </footer>
            </div>
            <nav className="shell-bottom" aria-label="Main navigation">
                {links}
            </nav>
        </div>
    )
}
