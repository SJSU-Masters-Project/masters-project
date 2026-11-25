// Skill-based job matching for the CareerMatch page. Everything here is computed from real API data:
// a candidate's profile skills (from their chips sections) and each job's required skills.
//
// Alignment is the share of a job's *required* skills that are on the profile:
//   round(100 × matched required skills ÷ required skills)
// Matching is case-insensitive. A job with no required skills has no alignment to show.

const lower = (s) =>
    String(s || '')
        .trim()
        .toLowerCase()

const requiredSkills = (job) => (job.skills || []).filter((s) => s.required).map((s) => s.name)

// Analyses one job against the set of profile skill names (already lowercased).
export function analyzeJob(job, profileSkillSet) {
    const required = requiredSkills(job)
    const matched = required.filter((name) => profileSkillSet.has(lower(name)))
    const missing = required.filter((name) => !profileSkillSet.has(lower(name)))
    const alignment = required.length === 0 ? null : Math.round((matched.length / required.length) * 100)
    return { ...job, required, matched, missing, alignment }
}

export const profileSkillSet = (skills) => new Set((skills || []).map(lower))

// All jobs analysed and sorted by alignment, highest first. Jobs without required skills sort last.
export function rankJobs(jobs, skills) {
    const set = profileSkillSet(skills)
    return (jobs || []).map((job) => analyzeJob(job, set)).sort((a, b) => (b.alignment ?? -1) - (a.alignment ?? -1))
}

// "Suggested" jobs: open jobs sharing at least one required skill with the profile.
export const isSuggested = (analyzed) => analyzed.matched.length > 0

export const STRONG_ALIGNMENT = 80

// A plain-language "why suggested" line built from the matched skills. Never a fixed string.
export function whyLine(analyzed) {
    const skills = analyzed.matched
    if (skills.length === 0) return 'This role is open; add matching skills to your profile to see how you line up.'
    if (skills.length === 1) return `Your ${skills[0]} matches a required skill for this role.`
    if (skills.length === 2) return `Your ${skills[0]} and ${skills[1]} match required skills for this role.`
    const head = skills.slice(0, 3).join(', ')
    return `Your ${head} and other skills match requirements for this role.`
}

// The six profile-completeness checks, in order. The caption names the first unfilled one.
// 1 full name, 2 headline, 3 education with at least one item, 4 a chips section,
// 5 a cards section, 6 a linked resume.
export function completeness(profile) {
    const p = profile || {}
    const sections = p.sections || []
    const hasTemplate = (name) => sections.some((s) => s.template === name && (s.data || []).length > 0)
    const checks = [
        { label: 'your full name', done: Boolean(p.personal?.fullName?.trim()) },
        { label: 'a headline', done: Boolean(p.career?.headline?.trim()) },
        { label: 'your education', done: Boolean(p.education?.data?.length) },
        { label: 'a skills section', done: hasTemplate('chips') },
        { label: 'a projects section', done: hasTemplate('cards') },
        { label: 'a linked resume', done: Boolean(p.career?.resumeId) },
    ]
    const done = checks.filter((c) => c.done).length
    const percent = Math.round((done / checks.length) * 100)
    const firstMissing = checks.find((c) => !c.done)?.label || null
    return { percent, done, total: checks.length, firstMissing }
}

// Distinct growth areas (missing required skills) across the suggested jobs, in order of first sighting.
export function growthAreas(analyzedJobs) {
    const seen = new Set()
    const out = []
    for (const job of analyzedJobs) {
        if (!isSuggested(job)) continue
        for (const skill of job.missing) {
            const k = lower(skill)
            if (k && !seen.has(k)) {
                seen.add(k)
                out.push(skill)
            }
        }
    }
    return out
}

// The career-plan actions, built from the real growth areas. Empty when there is nothing to improve.
export function careerPlan(analyzedJobs) {
    const areas = growthAreas(analyzedJobs)
    if (areas.length === 0) return []
    const top = areas.slice(0, 3)
    const steps = top.map((skill) => `Build a project using ${skill}`)
    steps.push(`Practice interview questions on ${top[0]}`)
    steps.push('Strengthen your portfolio')
    return steps
}
