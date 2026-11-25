import { splitList } from '../format'
import { chipSkillNames, normalizeSection } from './templates'

// Converts between the profile document the API returns and the shapes the profile page edits.
// Edited sections carry client-only `_key` values (React list keys). They are removed before saving,
// so the stored data is exactly Prof. Dhar's envelope and item shapes.

const KEY = '_key'
let counter = 0
const newKey = () => `k${Date.now().toString(36)}${(counter++).toString(36)}`

const isObject = (v) => v !== null && typeof v === 'object' && !Array.isArray(v)

// Adds a `_key` to an object and to every object inside its arrays (items, chip skills).
function addKeys(value) {
    if (Array.isArray(value)) return value.map(addKeys)
    if (!isObject(value)) return value
    const out = {}
    for (const [k, v] of Object.entries(value)) out[k] = addKeys(v)
    out[KEY] = newKey()
    return out
}

// Removes every `_key`, however deep.
export function stripKeys(value) {
    if (Array.isArray(value)) return value.map(stripKeys)
    if (!isObject(value)) return value
    const out = {}
    for (const [k, v] of Object.entries(value)) if (k !== KEY) out[k] = stripKeys(v)
    return out
}

export const withKeys = addKeys

// Profile document -> { education, sections } ready for editing. `education` is null until the user adds some.
export function fromProfile(doc) {
    const envelope = (s) => ({ ...s, [KEY]: newKey(), data: (s.data || []).map(addKeys) })
    return {
        education: isObject(doc?.education) ? envelope(doc.education) : null,
        sections: Array.isArray(doc?.sections) ? doc.sections.map(envelope) : [],
    }
}

// The name of every chips skill, unique ignoring case. Skills over 100 characters, or more than
// 100 of them, are left out because the shared profile contract caps `career.skills` there.
export function deriveSkills(sections) {
    return chipSkillNames(sections)
        .filter((name) => name.length <= 100)
        .slice(0, 100)
}

const cleanSection = (s) => normalizeSection(stripKeys(s))
const cleanEducation = (s) => normalizeSection(stripKeys(s), { isEducation: true })

export const blankForm = {
    fullName: '',
    phone: '',
    location: '',
    headline: '',
    summary: '',
    resumeId: '',
    targetRoles: '',
    employmentTypes: [],
    workModes: [],
    preferredLocations: '',
    willingToRelocate: false,
    visibility: 'private',
}

// Profile document -> editable form values for the About you, Career, Preferences and Visibility cards.
export function toForm(profile) {
    const p = profile.personal || {}
    const c = profile.career || {}
    const j = profile.jobPreferences || {}
    return {
        fullName: p.fullName || '',
        phone: p.phone || '',
        location: p.location || '',
        headline: c.headline || '',
        summary: c.summary || '',
        resumeId: c.resumeId || '',
        targetRoles: (j.targetRoles || []).join(', '),
        employmentTypes: j.employmentTypes || [],
        workModes: j.workModes || [],
        preferredLocations: (j.preferredLocations || []).join(', '),
        willingToRelocate: Boolean(j.willingToRelocate),
        visibility: profile.visibility || 'private',
    }
}

const drop = (obj) => Object.fromEntries(Object.entries(obj).filter(([, v]) => v !== '' && v !== undefined))

// Form values + sections -> the full request body. Fields the form does not edit (experience, projects,
// availableFrom, ...) are carried over from the saved profile so they are not lost. `career.skills` is
// always the unique skill names from every chips section, so job matching and the v1 export keep working.
export function toBody(form, sections, education, existing, email) {
    const personal = { ...(existing?.personal || {}), email: existing?.personal?.email || email, fullName: form.fullName.trim() }
    personal.phone = form.phone.trim()
    personal.location = form.location.trim()
    const career = {
        ...(existing?.career || {}),
        headline: form.headline.trim(),
        summary: form.summary.trim(),
        skills: deriveSkills(sections),
        resumeId: form.resumeId,
    }
    const prefs = {
        ...(existing?.jobPreferences || {}),
        targetRoles: splitList(form.targetRoles),
        employmentTypes: form.employmentTypes,
        workModes: form.workModes,
        preferredLocations: splitList(form.preferredLocations),
        willingToRelocate: form.willingToRelocate,
    }
    if (prefs.preferredLocations.length === 0) delete prefs.preferredLocations
    const body = {
        visibility: form.visibility,
        personal: drop(personal),
        career: drop(career),
        jobPreferences: prefs,
        sections: (sections || []).map(cleanSection),
    }
    if (education) body.education = cleanEducation(education)
    return body
}

// Body for saving only the custom sections: the whole array, plus the career block with fresh skills.
export function toSectionsPatch(sections, existing) {
    return {
        sections: sections.map(cleanSection),
        career: drop({ ...(existing?.career || {}), skills: deriveSkills(sections) }),
    }
}

// Body for saving only the education section.
export function toEducationPatch(education) {
    return { education: cleanEducation(education) }
}
