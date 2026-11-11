import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { SESSION_EXPIRED } from './api'
import { clearSession, loadSession } from './auth'
import { navigate } from './router'

const SessionContext = createContext(null)

export function SessionProvider({ children }) {
    const [session, setSession] = useState(() => loadSession())

    useEffect(() => {
        const expired = () => setSession(null)
        window.addEventListener(SESSION_EXPIRED, expired)
        return () => window.removeEventListener(SESSION_EXPIRED, expired)
    }, [])

    const refresh = useCallback(() => setSession(loadSession()), [])
    const signOut = useCallback(() => {
        clearSession()
        setSession(null)
        navigate('/login')
    }, [])

    const value = useMemo(
        () => ({
            session,
            user: session?.user || null,
            isLoggedIn: Boolean(session?.user),
            isCandidate: session?.user?.role === 'candidate',
            isEmployer: session?.user?.role === 'employer',
            refresh,
            signOut,
        }),
        [session, refresh, signOut]
    )
    return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>
}

export const useSession = () => useContext(SessionContext)
