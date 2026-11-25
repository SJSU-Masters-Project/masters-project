import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { useAuth, useClerk } from '@clerk/react'
import { api, setTokenProvider } from './api'
import { AccountError, RoleChoice } from './RoleGate'

const SessionContext = createContext(null)

export function SessionProvider({ children }) {
    const { isLoaded, isSignedIn, getToken, userId } = useAuth()
    const { signOut: clerkSignOut } = useClerk()
    const [account, setAccount] = useState({ userId: null, user: null, error: null })
    const [attempt, setAttempt] = useState(0)
    setTokenProvider(() => (isSignedIn ? getToken() : Promise.resolve(null)))

    useEffect(() => {
        let active = true
        if (isLoaded && !isSignedIn) setAccount({ userId: null, user: null, error: null })
        if (isLoaded && isSignedIn) {
            api('/me').then(
                (user) => {
                    if (active) setAccount({ userId, user, error: null })
                },
                (error) => {
                    if (active) setAccount({ userId, user: null, error: error.message })
                }
            )
        }
        return () => {
            active = false
        }
    }, [isLoaded, isSignedIn, userId, attempt])

    const signOut = useCallback(() => clerkSignOut({ redirectUrl: '/' }), [clerkSignOut])
    const user = isSignedIn && account.userId === userId ? account.user : null
    const value = useMemo(
        () => ({
            user,
            isLoggedIn: Boolean(user),
            isCandidate: user?.role === 'candidate',
            isEmployer: user?.role === 'employer',
            signOut,
        }),
        [user, signOut]
    )

    if (!isLoaded) return null
    if (isSignedIn && account.userId !== userId) return <p>Loading your account…</p>
    if (isSignedIn && account.error) return <AccountError message={account.error} onRetry={() => setAttempt((n) => n + 1)} />
    if (isSignedIn && user && !user.role) {
        const choose = async (role) => {
            try {
                const updated = await api('/me/role', { method: 'POST', body: { role } })
                setAccount({ userId, user: updated, error: null })
            } catch (error) {
                if (error.status === 409) {
                    setAttempt((n) => n + 1)
                    return
                }
                throw error
            }
        }
        return <RoleChoice onChoose={choose} />
    }
    return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>
}

export const useSession = () => useContext(SessionContext)
