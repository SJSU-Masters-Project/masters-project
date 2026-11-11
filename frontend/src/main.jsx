import React from 'react'
import { createRoot } from 'react-dom/client'
import LoginPage from './LoginPage'
import Shell, { useTheme } from './Shell'
import { SessionProvider, useSession } from './session'
import { Link, matchPath, navigate, useLocation } from './router'
import { EmptyState, Page } from './ui'
import EmployerPage from './pages/EmployerPage'
import JobDetailPage from './pages/JobDetailPage'
import JobsPage from './pages/JobsPage'
import CareerMatchPage from './pages/CareerMatchPage'
import ProfilePage from './pages/ProfilePage'
import ResumesPage from './pages/ResumesPage'
import './theme.css'

function NotFound() {
    return (
        <Page>
            <EmptyState
                action={
                    <Link to="/jobs" className="btn contained">
                        Browse jobs
                    </Link>
                }
            >
                We could not find that page.
            </EmptyState>
        </Page>
    )
}

function Routes({ path }) {
    const job = matchPath('/jobs/:id', path)
    if (path === '/' || path === '/jobs') return <JobsPage />
    if (job) return <JobDetailPage key={job.id} id={job.id} />
    if (path === '/career-match') return <CareerMatchPage />
    if (path === '/profile') return <ProfilePage />
    if (path === '/resumes') return <ResumesPage />
    if (path === '/employer') return <EmployerPage />
    return <NotFound />
}

function Root() {
    const { path } = useLocation()
    const { isLoggedIn, refresh } = useSession()
    const [theme, toggleTheme] = useTheme()

    if (path === '/login') {
        // A signed-in visitor has no reason to see the login form.
        if (isLoggedIn) {
            queueMicrotask(() => navigate('/', { replace: true }))
            return null
        }
        return (
            <LoginPage
                onSignedIn={() => {
                    refresh()
                    navigate('/')
                }}
            />
        )
    }
    return (
        <Shell path={path} theme={theme} toggleTheme={toggleTheme}>
            <Routes path={path} />
        </Shell>
    )
}

createRoot(document.getElementById('root')).render(
    <SessionProvider>
        <Root />
    </SessionProvider>
)
