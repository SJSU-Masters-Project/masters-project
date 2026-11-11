import React from 'react'
import { SignIn, SignUp } from '@clerk/react'
import './login.css'

// Sign-in, sign-up and password reset are Clerk's components; the API has no login endpoints.
// Hash routing keeps Clerk's own steps (e.g. /login#/factor-one) on one page, so the simple
// path check in main.jsx is all the routing the app needs.

export function LoginPage() {
    return (
        <div className="login-page">
            <SignIn routing="hash" signUpUrl="/sign-up" fallbackRedirectUrl="/" />
        </div>
    )
}

export function SignUpPage() {
    return (
        <div className="login-page">
            <SignUp routing="hash" signInUrl="/login" fallbackRedirectUrl="/" />
        </div>
    )
}
