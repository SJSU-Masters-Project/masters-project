import React, { useState } from 'react'
import { AlertCircle, ArrowRight, Loader2, LogIn, Mail } from 'lucide-react'
import { devToken, fetchMe, LoginError, saveSession } from './auth'
import './login.css'

const ROLES = [
    { value: 'candidate', label: 'Student / candidate' },
    { value: 'employer', label: 'Employer' },
]

export default function LoginPage({ onSignedIn }) {
    const [email, setEmail] = useState('')
    const [role, setRole] = useState('candidate')
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)

    const signIn = async (event) => {
        event?.preventDefault()
        if (loading) return
        setLoading(true)
        setError(null)
        try {
            const token = devToken(email, role)
            const user = await fetchMe(token)
            saveSession({ token, user })
            onSignedIn(user)
        } catch (err) {
            setError(
                err instanceof LoginError
                    ? { message: err.message, retry: err.kind === 'network' }
                    : { message: 'Something went wrong. Please try again.', retry: true }
            )
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="login-page">
            <main className="login-card" aria-labelledby="login-title">
                <div className="login-wordmark">
                    <em>my</em>Academic
                </div>
                <h1 id="login-title" className="login-title">
                    <LogIn className="login-title-icon" size={28} /> Log in
                </h1>
                <p className="login-subtitle">Sign in to find roles, manage your profile and track applications.</p>

                <form onSubmit={signIn}>
                    <label className="login-label" htmlFor="login-email">
                        Email address
                    </label>
                    <div className="login-input-wrap">
                        <Mail size={16} aria-hidden="true" />
                        <input
                            id="login-email"
                            className="login-input"
                            type="email"
                            autoComplete="email"
                            required
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            placeholder="you@university.edu"
                            disabled={loading}
                        />
                    </div>

                    <span className="login-label" id="login-role-label">
                        I am a
                    </span>
                    <div className="login-roles" role="radiogroup" aria-labelledby="login-role-label">
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
                            <span>{error.message}</span>
                            {error.retry && (
                                <button type="button" className="login-btn outlined small" onClick={signIn}>
                                    Retry
                                </button>
                            )}
                        </div>
                    )}

                    <button type="submit" className="login-btn contained" disabled={loading || !email}>
                        {loading ? (
                            <>
                                <Loader2 className="login-spin" size={16} aria-hidden="true" /> Signing in…
                            </>
                        ) : (
                            <>
                                Continue <ArrowRight size={16} aria-hidden="true" />
                            </>
                        )}
                    </button>
                </form>

                <p className="login-note">Development sign-in. Production uses your institution account.</p>
            </main>
        </div>
    )
}
