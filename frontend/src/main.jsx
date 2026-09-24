import React, { useMemo, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { ArrowRight, Bell, BriefcaseBusiness, Building2, CalendarDays, Check, ChevronDown, GraduationCap, Heart, MapPin, Search, Sparkles, Users } from 'lucide-react'
import './styles.css'

const jobs = [
  { id: 1, title: 'Product Design Intern', company: 'Northstar Health', location: 'Remote · United States', type: 'Internship', salary: '$28–32/hr', accent: 'blue', logo: 'N' },
  { id: 2, title: 'Frontend Engineer', company: 'Lumen Labs', location: 'San Francisco, CA · Hybrid', type: 'Full-time', salary: '$110k–135k', accent: 'orange', logo: 'L' },
  { id: 3, title: 'Research Assistant', company: 'Goodfield University', location: 'New York, NY · On-site', type: 'Part-time', salary: '$24–28/hr', accent: 'gold', logo: 'G' },
]

function BrandMark() { return <span className="brand-mark" aria-hidden="true"><span>MA</span></span> }

function App() {
  const [view, setView] = useState('students')
  const [query, setQuery] = useState('')
  const [saved, setSaved] = useState([])
  const [email, setEmail] = useState('')
  const [subscribed, setSubscribed] = useState(false)
  const filteredJobs = useMemo(() => jobs.filter(job => `${job.title} ${job.company} ${job.location}`.toLowerCase().includes(query.toLowerCase())), [query])
  const toggleSaved = id => setSaved(current => current.includes(id) ? current.filter(item => item !== id) : [...current, id])

  return <div className="app-shell">
    <aside className="sidebar">
      <div className="sidebar-brand"><BrandMark /><span>myAcademic</span></div><div className="sidebar-rule" />
      <nav className="side-nav" aria-label="Main navigation">
        <a className="side-link active" href="#home"><BriefcaseBusiness size={19} /><span>Career home</span></a><a className="side-link" href="#roles"><Search size={19} /><span>Browse roles</span></a><a className="side-link" href="#how-it-works"><GraduationCap size={19} /><span>Career toolkit</span></a><a className="side-link" href="#employers"><Building2 size={19} /><span>For employers</span></a>
      </nav>
      <div className="sidebar-bottom"><button className="notification" aria-label="Notifications"><Bell size={19} /><i>3</i></button><button className="avatar" aria-label="Open profile">EC</button></div>
    </aside>
    <div className="page-shell">
      <header className="topbar"><div className="mobile-brand"><BrandMark /><strong>myAcademic</strong></div><div className="topbar-spacer" /><span className="date-chip"><CalendarDays size={15} /> Wednesday · September 23, 2026</span><button className="ta-button"><Sparkles size={15} /> Virtual TA</button></header>
      <main>
        <section className="hero" id="home"><div className="hero-copy"><div className="eyebrow"><span className="eyebrow-dot" /> Your next chapter starts here</div><h1>Find work that moves you <em>forward.</em></h1><p className="hero-lede">A career home for students, graduates, and the companies looking for their next great hire.</p><div className="hero-actions"><a className="primary-button" href="#roles">Explore opportunities <ArrowRight size={18} /></a><a className="secondary-link" href="#employers">I’m hiring <ArrowRight size={16} /></a></div></div>
          <div className="hero-visual" aria-label="Career opportunities overview"><div className="visual-orbit orbit-a" /><div className="visual-orbit orbit-b" /><div className="opportunity-card"><div className="opportunity-top"><span className="status-dot" /> Recommended for you <span>✦</span></div><div className="company-line"><div className="company-logo northstar">N</div><div><strong>Northstar Health</strong><small>Health technology</small></div></div><h3>Product Design Intern</h3><div className="job-meta"><span><MapPin size={14} /> Remote</span><span>Summer 2026</span></div><button className="save-button" onClick={() => toggleSaved(1)}><Heart size={16} fill={saved.includes(1) ? 'currentColor' : 'none'} /> {saved.includes(1) ? 'Saved' : 'Save role'}</button></div><div className="visual-note note-one"><strong>24,812</strong><span>students finding their fit</span></div><div className="visual-note note-two"><Check size={14} /> Human-first matching</div></div>
        </section>
        <section className="role-switcher" id="how-it-works"><div><span className="section-label">START WHERE YOU ARE</span><h2>Built for your next move.</h2></div><div className="switcher-buttons"><button className={view === 'students' ? 'selected' : ''} onClick={() => setView('students')}><GraduationCap size={18} /> I’m a student</button><button className={view === 'employers' ? 'selected' : ''} onClick={() => setView('employers')}><Building2 size={18} /> I’m an employer</button></div><div className="switcher-copy">{view === 'students' ? <><strong>Discover opportunities made for your path.</strong><span>Search internships and early-career roles, save the ones that feel right, and keep your momentum going.</span><a href="#roles">Find your next role <ArrowRight size={15} /></a></> : <><strong>Meet the people who will move your team forward.</strong><span>Tell your story, share your open roles, and connect with students ready to do meaningful work.</span><a href="#employers">Start hiring <ArrowRight size={15} /></a></>}</div></section>
        <section className="roles-section" id="roles"><div className="section-heading"><div><span className="section-label">01 / OPPORTUNITIES</span><h2>Worth a look.</h2></div><a className="view-all" href="#roles">View all roles <ArrowRight size={16} /></a></div><div className="search-row"><div className="search-box"><Search size={18} /><input value={query} onChange={e => setQuery(e.target.value)} placeholder="Search by role, company, or location" /></div><button className="filter-button">All opportunities <ChevronDown size={16} /></button></div><div className="job-list">{filteredJobs.length ? filteredJobs.map(job => <article className="job-row" key={job.id}><div className={`company-logo ${job.accent}`}>{job.logo}</div><div className="job-main"><div className="job-title-line"><h3>{job.title}</h3><span className="job-type">{job.type}</span></div><p>{job.company} <span>·</span> {job.location}</p></div><span className="job-salary">{job.salary}</span><button className={`row-save ${saved.includes(job.id) ? 'saved' : ''}`} onClick={() => toggleSaved(job.id)} aria-label={`Save ${job.title}`}><Heart size={17} fill={saved.includes(job.id) ? 'currentColor' : 'none'} /></button><ArrowRight className="row-arrow" size={18} /></article>) : <div className="empty-state">No roles match “{query}”. Try a broader search.</div>}</div></section>
        <section className="employer-banner" id="employers"><div className="banner-icon"><Users size={23} /></div><div><span className="section-label">FOR COMPANIES</span><h2>Good teams start with the right people.</h2><p>Reach students and graduates who are ready to make an impact.</p></div><a className="light-button" href="mailto:hiring@myacademic.org">Post an opportunity <ArrowRight size={17} /></a></section>
        <section className="newsletter"><div><span className="section-label">STAY IN THE LOOP</span><h2>Opportunities, delivered.</h2><p>A short, useful roundup of new roles and career resources. No noise.</p></div>{subscribed ? <div className="subscribed"><Check size={20} /><strong>You’re on the list.</strong><span>We’ll send the next good thing your way.</span></div> : <form onSubmit={e => { e.preventDefault(); if (email) setSubscribed(true) }}><label htmlFor="email">Your email address</label><div className="newsletter-input"><input id="email" type="email" required value={email} onChange={e => setEmail(e.target.value)} placeholder="you@example.com" /><button type="submit" aria-label="Subscribe"><ArrowRight size={18} /></button></div></form>}</section>
      </main>
      <footer><div className="footer-brand"><BrandMark /><strong>myAcademic</strong></div><span>Learn well. Work meaningfully.</span><span>© 2026 myAcademic</span></footer>
    </div>
  </div>
}

createRoot(document.getElementById('root')).render(<App />)
