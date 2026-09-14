import React, { useState } from 'react'
import { createRoot } from 'react-dom/client'
import { ArrowUpRight, BriefcaseBusiness, Building2, Check, GraduationCap, MapPin, Search, Sparkles } from 'lucide-react'
import './styles.css'

const roles = { candidate: { label: 'Job seeker', icon: GraduationCap, eyebrow: 'Find work that fits your life', title: 'Your next chapter starts here.', copy: 'A calmer way to search, apply, and keep moving forward.', cta: 'Explore open roles' }, company: { label: 'Company', icon: Building2, eyebrow: 'Build your next great team', title: 'Meet people who move things forward.', copy: 'Share the work worth doing and find the people ready to do it.', cta: 'Post a role' } }
const jobs = [
  { title: 'Product Designer', company: 'Lumen Labs', location: 'San Francisco · Hybrid', type: 'Full-time', color: 'coral' },
  { title: 'Frontend Engineer', company: 'Northstar Health', location: 'Remote · US only', type: 'Full-time', color: 'blue' },
  { title: 'Community Lead', company: 'Goodfield', location: 'New York · On-site', type: 'Full-time', color: 'yellow' },
]

function App() {
  const [role, setRole] = useState('candidate')
  const [email, setEmail] = useState('')
  const [submitted, setSubmitted] = useState(false)
  const active = roles[role]
  const Icon = active.icon
  return <main className="shell">
    <nav><div className="brand"><span className="brand-mark">↗</span> wayfinder</div><div className="nav-links"><a href="#roles">Browse roles</a><a href="#about">How it works</a><button className="nav-login">Sign in</button></div></nav>
    <section className="hero"><div className="hero-copy"><div className="eyebrow"><Sparkles size={15}/> A better way to get hired</div><h1>Good work<br/><em>finds</em> good people.</h1><p className="lede">Wayfinder brings ambitious people and thoughtful companies together — with a little less noise in between.</p><div className="hero-actions"><button className="button button-dark" onClick={() => document.getElementById('roles').scrollIntoView({ behavior: 'smooth' })}>Start exploring <ArrowUpRight size={18}/></button><span className="quiet-note">No endless applications. Promise.</span></div></div><div className="hero-art"><div className="orbit orbit-one"></div><div className="orbit orbit-two"></div><div className="art-card"><span className="card-kicker">A note for today</span><strong>Make room for<br/><span>the right fit.</span></strong><div className="scribble">✳</div></div><div className="floating-tag tag-top">✦ 24,812 people hired</div><div className="floating-tag tag-bottom">→ human-first matching</div></div></section>
    <section className="role-section" id="roles"><div className="section-intro"><span className="section-number">01 /</span><h2>Where are you<br/>headed?</h2></div><div className="role-grid">{Object.entries(roles).map(([key, item]) => { const RoleIcon = item.icon; return <button key={key} className={`role-card ${role === key ? 'selected' : ''}`} onClick={() => { setRole(key); setSubmitted(false) }}><div className="role-icon"><RoleIcon size={22}/></div><div><span className="role-label">I’m a {item.label.toLowerCase()}</span><h3>{item.cta}</h3><p>{key === 'candidate' ? 'Search roles with space to grow.' : 'Tell your story to the right candidates.'}</p></div><ArrowUpRight className="role-arrow" size={20}/></button> })}</div></section>
    <section className="portal"><div className="portal-heading"><span className="section-number">02 / YOUR PORTAL</span><h2>{active.title}</h2><p>{active.copy}</p></div><div className="login-panel"><div className="panel-top"><div className="mini-icon"><Icon size={18}/></div><span>Continue as a {active.label.toLowerCase()}</span></div>{submitted ? <div className="success"><div className="success-icon"><Check/></div><h3>You’re on your way.</h3><p>We’ll use this email to create your {active.label.toLowerCase()} profile.</p><button className="text-button" onClick={() => setSubmitted(false)}>Use another email</button></div> : <form onSubmit={e => { e.preventDefault(); if (email) setSubmitted(true) }}><label>Email address</label><div className="input-row"><input type="email" placeholder="you@example.com" value={email} onChange={e => setEmail(e.target.value)} required/><button className="button button-orange">Continue <ArrowUpRight size={17}/></button></div><div className="form-foot"><span>Already have an account?</span><button type="button" className="text-button">Sign in</button></div></form>}</div></section>
    <section className="featured"><div className="featured-top"><div><span className="section-number">03 / JUST IN</span><h2>Worth a look.</h2></div><button className="browse-button">See all roles <ArrowUpRight size={17}/></button></div><div className="job-list">{jobs.map(job => <article className="job-row" key={job.title}><div className={`job-dot ${job.color}`}></div><div className="job-main"><h3>{job.title}</h3><p>{job.company} <span>·</span> {job.location}</p></div><span className="job-type">{job.type}</span><ArrowUpRight className="row-arrow" size={19}/></article>)}</div></section>
    <footer><div className="brand"><span className="brand-mark">↗</span> wayfinder</div><span>Made for the next good thing.</span><span>© 2025 Wayfinder</span></footer>
  </main>
}
createRoot(document.getElementById('root')).render(<App />)

