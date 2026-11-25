import React, { useEffect, useState } from 'react'

// A tiny History API router: the portal has a handful of routes and no nested layouts.
export function navigate(to, { replace = false } = {}) {
    window.history[replace ? 'replaceState' : 'pushState']({}, '', to)
    window.dispatchEvent(new PopStateEvent('popstate'))
    window.scrollTo(0, 0)
}

export function useLocation() {
    const [loc, setLoc] = useState({ path: window.location.pathname, search: window.location.search })
    useEffect(() => {
        const onPop = () => setLoc({ path: window.location.pathname, search: window.location.search })
        window.addEventListener('popstate', onPop)
        return () => window.removeEventListener('popstate', onPop)
    }, [])
    return loc
}

export function Link({ to, children, onClick, ...rest }) {
    const handle = (event) => {
        onClick?.(event)
        if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey) return
        event.preventDefault()
        navigate(to)
    }
    return (
        <a href={to} onClick={handle} {...rest}>
            {children}
        </a>
    )
}

// Matches "/jobs/:id" style patterns. Returns the params object or null.
export function matchPath(pattern, path) {
    const a = pattern.split('/').filter(Boolean)
    const b = path.split('/').filter(Boolean)
    if (a.length !== b.length) return null
    const params = {}
    for (let i = 0; i < a.length; i += 1) {
        if (a[i].startsWith(':')) params[a[i].slice(1)] = decodeURIComponent(b[i])
        else if (a[i] !== b[i]) return null
    }
    return params
}
