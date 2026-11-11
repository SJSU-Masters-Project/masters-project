import React, { useEffect, useState } from 'react'
import { SignOutButton } from '@clerk/react'
import { AlertCircle, ArrowRight, Loader2 } from 'lucide-react'
import { useApi } from './api'
import './login.css'

const ROLES = [
    { value: 'candidate', label: 'Student / candidate' },
    { value: 'employer', label: 'Employer' },
]

// Wraps the portal for signed-in users. The API creates a Clerk user with no role on their first
// request; they choose candidate or employer once (POST /api/v1/me/role) before going further.
// The portal stays on screen while /api/v1/me loads, so returning users see no flash.
export default function RoleGate({ children }) {
    const api = useApi()
    const [me, setMe] = useState(null)
    const [error, setError] = useState(null)

    const load = () => {
        setError(null)
        api('/v1/me').then(setMe, (err) => setError(err.message))
    }
    useEffect(load, [])

    const choose = async (role) => {
        try {
            setMe(await api('/v1/me/role', { method: 'POST', body: JSON.stringify({ role }) }))
        } catch (err) {
            if (err.status === 409) return load() // already chosen, e.g. in another tab
            throw err
        }
    }

    if (error) return <AccountError message={error} onRetry={load} />
    if (me && !me.role) return <RoleChoice onChoose={choose} />
    return children
}

function RoleChoice({ onChoose }) {
    const [role, setRole] = useState('candidate')
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)

    const submit = async (event) => {
        event.preventDefault()
        if (loading) return
        setLoading(true)
        setError(null)
        try {
            await onChoose(role)
        } catch (err) {
            setError(err.message)
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="login-page">
            <main className="login-card" aria-labelledby="role-title">
                <div className="login-wordmark">
                    <em>my</em>Academic
                </div>
                <h1 id="role-title" className="login-title">
                    One last step
                </h1>
                <p className="login-subtitle">How will you use myAcademic? You can't change this later.</p>

                <form onSubmit={submit}>
                    <span className="login-label" id="role-label">
                        I am a
                    </span>
                    <div className="login-roles" role="radiogroup" aria-labelledby="role-label">
                        {ROLES.map((r) => (
                            <button
                                key={r.value}
                                type="button"
                                role="radio"
                                aria-checked={role === r.value}
                                className={`login-role${role === r.value ? ' selected' : ''}`}
                                onClick={() => setRole(r.value)}
                                disabled={loading}
                            >
                                {r.label}
                            </button>
                        ))}
                    </div>

                    {error && (
                        <div className="login-error" role="alert">
                            <AlertCircle size={16} aria-hidden="true" />
                            <span>{error}</span>
                        </div>
                    )}

                    <button type="submit" className="login-btn contained" disabled={loading}>
                        {loading ? (
                            <>
                                <Loader2 className="login-spin" size={16} aria-hidden="true" /> Saving…
                            </>
                        ) : (
                            <>
                                Continue <ArrowRight size={16} aria-hidden="true" />
                            </>
                        )}
                    </button>
                </form>
                {/* The role is permanent, so someone who signed in with the wrong account must be
                    able to leave without choosing one. */}
                <SignOutButton>
                    <button type="button" className="login-btn outlined block" disabled={loading}>
                        Not you? Sign out
                    </button>
                </SignOutButton>
            </main>
        </div>
    )
}

// Shown when the API rejects a signed-in user (e.g. the Clerk instance is missing the "email"
// session-token claim) or cannot be reached, so the user is never stuck on a blank page.
function AccountError({ message, onRetry }) {
    return (
        <div className="login-page">
            <main className="login-card" aria-labelledby="account-error-title">
                <div className="login-wordmark">
                    <em>my</em>Academic
                </div>
                <h1 id="account-error-title" className="login-title">
                    We couldn't load your account
                </h1>
                <div className="login-error" role="alert">
                    <AlertCircle size={16} aria-hidden="true" />
                    <span>{message}</span>
                </div>
                <button type="button" className="login-btn contained" onClick={onRetry}>
                    Try again
                </button>
                <SignOutButton>
                    <button type="button" className="login-btn outlined block">
                        Sign out
                    </button>
                </SignOutButton>
            </main>
        </div>
    )
}
