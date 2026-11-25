import React from 'react'
import { createRoot } from 'react-dom/client'
import { ClerkProvider } from '@clerk/react'
import { LoginPage, SignUpPage } from './LoginPage'
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
    const { isLoggedIn } = useSession()
    const [theme, toggleTheme] = useTheme()

    if (path === '/login' || path === '/sign-up') {
        if (isLoggedIn) {
            queueMicrotask(() => navigate('/', { replace: true }))
            return null
        }
        return path === '/login' ? <LoginPage /> : <SignUpPage />
    }
    return (
        <Shell path={path} theme={theme} toggleTheme={toggleTheme}>
            <Routes path={path} />
        </Shell>
    )
}

const clerkKey = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY
if (!clerkKey) throw new Error('Set VITE_CLERK_PUBLISHABLE_KEY in frontend/.env.local (see README).')

createRoot(document.getElementById('root')).render(
    <ClerkProvider publishableKey={clerkKey} signInUrl="/login" signUpUrl="/sign-up" afterSignOutUrl="/">
        <SessionProvider>
            <Root />
        </SessionProvider>
    </ClerkProvider>
)
