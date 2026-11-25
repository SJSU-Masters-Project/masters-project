import { Award, GraduationCap, History, LayoutGrid, Link2, Tags, TextCursorInput } from 'lucide-react'
import { isIsoDate } from './dates'
import { safeUrl, sanitize } from './safeHtml'

// The registry of Prof. Dhar's section templates. Each entry knows how to make an empty item,
// clean an item up for saving (`normalize`) and report what is wrong with it (`validate`).
// Field names and shapes follow schema.js exactly.

export const TEMPLATE_NAMES = ['cards', 'timeline', 'list', 'chips', 'links', 'text']

const LINK_MESSAGE = 'Enter a link that starts with http:// or https://.'
const DATE_MESSAGE = 'Use a valid date (YYYY-MM-DD) or leave it empty.'

const isObject = (v) => v !== null && typeof v === 'object' && !Array.isArray(v)
const trimmed = (v) => (typeof v === 'string' ? v.trim() : '')
const blank = (v) => typeof v !== 'string' || v.trim() === ''

// Copies an optional string onto `out` only when it has content.
function putOptional(out, key, value) {
    const text = trimmed(value)
    if (text) out[key] = text
}

// Trims, drops empty entries and drops case-insensitive duplicates, keeping the first spelling.
function cleanStrings(list) {
    const seen = new Set()
    return (Array.isArray(list) ? list : []).map(trimmed).filter((s) => {
        const k = s.toLowerCase()
        if (!s || seen.has(k)) return false
        seen.add(k)
        return true
    })
}

function putStrings(out, key, list) {
    const cleaned = cleanStrings(list)
    if (cleaned.length) out[key] = cleaned
}

// '' and undefined become null; a value is kept as typed so validate can reject a bad one.
const dateOrNull = (v) =>
    v === undefined || v === null || (typeof v === 'string' && v.trim() === '') ? null : typeof v === 'string' ? v.trim() : v

function checkRequired(errors, item, key, label) {
    if (blank(item[key])) errors[key] = `${label} is required.`
}

function checkOptionalText(errors, item, key) {
    if (item[key] !== undefined && typeof item[key] !== 'string') errors[key] = 'Must be text.'
}

function checkLink(errors, item, key) {
    if (item[key] === undefined || item[key] === '') return
    if (typeof item[key] !== 'string' || !safeUrl(item[key])) errors[key] = LINK_MESSAGE
}

function checkDate(errors, item, key) {
    if (!(key in item)) errors[key] = DATE_MESSAGE
    else if (item[key] !== null && !isIsoDate(item[key])) errors[key] = DATE_MESSAGE
}

function checkStrings(errors, item, key) {
    if (item[key] === undefined) return
    if (!Array.isArray(item[key]) || item[key].some((s) => typeof s !== 'string' || s.trim() === ''))
        errors[key] = 'Must be a list of text values.'
}

function checkUnknown(errors, item, allowed) {
    for (const key of Object.keys(item)) {
        if (!allowed.includes(key) && !key.startsWith('_')) errors[key] = 'Unknown field.'
    }
}

function guard(item, allowed, run) {
    if (!isObject(item)) return { '': 'Must be an object.' }
    const errors = {}
    run(errors)
    checkUnknown(errors, item, allowed)
    return errors
}

const CARD_KEYS = ['title', 'purpose', 'link', 'techStack', 'features']
const TIMELINE_KEYS = ['title', 'subtitle', 'link', 'description', 'startDate', 'endDate']
const EDUCATION_KEYS = ['degree', 'institute', 'grade', 'link', 'startDate', 'endDate']
const LIST_KEYS = ['title', 'subtitle', 'link', 'date', 'description']
const CHIPS_KEYS = ['category', 'skillsList']
const SKILL_KEYS = ['skillName', 'proficiency']
const LINK_KEYS = ['name', 'url', 'description']

export const isProficiency = (v) => typeof v === 'number' && Number.isInteger(v) && v >= 1 && v <= 5

const cards = {
    label: 'Cards',
    icon: LayoutGrid,
    useCase: 'Projects, portfolio highlights, and accomplishments.',
    emptyItem: () => ({ title: '', purpose: '', link: '', techStack: [], features: [] }),
    normalize(item) {
        const out = { title: trimmed(item.title) }
        putOptional(out, 'purpose', item.purpose)
        putOptional(out, 'link', item.link)
        putStrings(out, 'techStack', item.techStack)
        putStrings(out, 'features', item.features)
        return out
    },
    validate: (item) =>
        guard(item, CARD_KEYS, (e) => {
            checkRequired(e, item, 'title', 'Title')
            checkOptionalText(e, item, 'purpose')
            checkLink(e, item, 'link')
            checkStrings(e, item, 'techStack')
            checkStrings(e, item, 'features')
        }),
}

const timeline = {
    label: 'Timeline',
    icon: History,
    useCase: 'Chronological records such as work experience.',
    emptyItem: () => ({ title: '', subtitle: '', link: '', description: '', startDate: null, endDate: null }),
    normalize(item) {
        const out = { title: trimmed(item.title), subtitle: trimmed(item.subtitle) }
        putOptional(out, 'link', item.link)
        putOptional(out, 'description', item.description)
        out.startDate = dateOrNull(item.startDate)
        out.endDate = dateOrNull(item.endDate)
        return out
    },
    validate: (item) =>
        guard(item, TIMELINE_KEYS, (e) => {
            checkRequired(e, item, 'title', 'Title')
            checkRequired(e, item, 'subtitle', 'Company or organization')
            checkLink(e, item, 'link')
            checkOptionalText(e, item, 'description')
            checkDate(e, item, 'startDate')
            checkDate(e, item, 'endDate')
        }),
}

// The top-level "education" section: the timeline template with its own field names.
const education = {
    label: 'Education',
    icon: GraduationCap,
    useCase: 'Degrees and schooling, shown first on your profile.',
    emptyItem: () => ({ degree: '', institute: '', grade: '', link: '', startDate: null, endDate: null }),
    normalize(item) {
        const out = { degree: trimmed(item.degree), institute: trimmed(item.institute) }
        putOptional(out, 'grade', item.grade)
        putOptional(out, 'link', item.link)
        out.startDate = dateOrNull(item.startDate)
        out.endDate = dateOrNull(item.endDate)
        return out
    },
    validate: (item) =>
        guard(item, EDUCATION_KEYS, (e) => {
            checkRequired(e, item, 'degree', 'Degree')
            checkRequired(e, item, 'institute', 'Institute')
            checkOptionalText(e, item, 'grade')
            checkLink(e, item, 'link')
            checkDate(e, item, 'startDate')
            checkDate(e, item, 'endDate')
        }),
}

const list = {
    label: 'List',
    icon: Award,
    useCase: 'Certifications, publications, and awards.',
    emptyItem: () => ({ title: '', subtitle: '', link: '', date: null, description: '' }),
    normalize(item) {
        const out = { title: trimmed(item.title) }
        putOptional(out, 'subtitle', item.subtitle)
        putOptional(out, 'link', item.link)
        out.date = dateOrNull(item.date)
        putOptional(out, 'description', item.description)
        return out
    },
    validate: (item) =>
        guard(item, LIST_KEYS, (e) => {
            checkRequired(e, item, 'title', 'Title')
            checkOptionalText(e, item, 'subtitle')
            checkLink(e, item, 'link')
            checkDate(e, item, 'date')
            checkOptionalText(e, item, 'description')
        }),
}

const chips = {
    label: 'Skill chips',
    icon: Tags,
    useCase: 'Categorized skills with proficiency scores.',
    emptyItem: () => ({ category: '', skillsList: [{ skillName: '', proficiency: 3 }] }),
    normalize(item) {
        const skills = (Array.isArray(item.skillsList) ? item.skillsList : [])
            .filter((s) => isObject(s) && !blank(s.skillName))
            .map((s) => ({ skillName: trimmed(s.skillName), proficiency: s.proficiency }))
        return { category: trimmed(item.category), skillsList: skills }
    },
    validate: (item) =>
        guard(item, CHIPS_KEYS, (e) => {
            checkRequired(e, item, 'category', 'Category')
            if (!Array.isArray(item.skillsList) || item.skillsList.length === 0) {
                e.skillsList = 'Add at least one skill.'
                return
            }
            item.skillsList.forEach((skill, i) => {
                if (!isObject(skill)) {
                    e[`skillsList.${i}`] = 'Must be an object.'
                    return
                }
                if (blank(skill.skillName)) e[`skillsList.${i}.skillName`] = 'Skill name is required.'
                if (!isProficiency(skill.proficiency)) e[`skillsList.${i}.proficiency`] = 'Choose a whole number from 1 to 5.'
                for (const key of Object.keys(skill)) {
                    if (!SKILL_KEYS.includes(key) && !key.startsWith('_')) e[`skillsList.${i}.${key}`] = 'Unknown field.'
                }
            })
        }),
}

const links = {
    label: 'Links',
    icon: Link2,
    useCase: 'Curated web links and personal resources.',
    emptyItem: () => ({ name: '', url: '', description: '' }),
    normalize(item) {
        const out = { name: trimmed(item.name), url: trimmed(item.url) }
        putOptional(out, 'description', item.description)
        return out
    },
    validate: (item) =>
        guard(item, LINK_KEYS, (e) => {
            checkRequired(e, item, 'name', 'Name')
            if (blank(item.url)) e.url = 'URL is required.'
            else if (!safeUrl(item.url)) e.url = LINK_MESSAGE
            checkOptionalText(e, item, 'description')
        }),
}

// "text": the section's data is one string, so the item is that string (HTML or plain text).
const text = {
    label: 'Rich text',
    icon: TextCursorInput,
    useCase: 'Freeform rich text introductions and custom summaries.',
    emptyItem: () => '',
    normalize: (item) => (typeof item === 'string' ? sanitize(item) : ''),
    validate: (item) => (typeof item === 'string' ? {} : { '': 'Must be text.' }),
}

export const TEMPLATES = { cards, timeline, list, chips, links, text }
export const EDUCATION = education

export const getTemplate = (name) => TEMPLATES[name]

export const newSection = (template, heading = '') => ({ heading, visible: true, template, data: template === 'text' ? [''] : [] })

export const newEducation = () => ({ heading: 'Education', visible: true, template: 'timeline', data: [] })

// The template definition for a section: education has its own field names.
const defFor = (section, isEducation) => (isEducation ? education : TEMPLATES[section?.template])

// Cleans a whole envelope for saving: exactly heading, visible, template and data.
export function normalizeSection(section, { isEducation = false } = {}) {
    const def = defFor(section, isEducation)
    const data = Array.isArray(section.data) ? section.data : []
    const cleaned = def ? data.map((item) => (isObject(item) || section.template === 'text' ? def.normalize(item) : item)) : data
    return {
        heading: isEducation ? 'Education' : trimmed(section.heading),
        visible: section.visible === true,
        template: isEducation ? 'timeline' : section.template,
        data: section.template === 'text' && !isEducation ? [cleaned[0] ?? ''] : cleaned,
    }
}

// Returns { 'data.0.title': 'message', ... } for a section, empty when it is valid.
// The section is cleaned first, so what is checked is what would be saved.
export function validateSection(section, { isEducation = false } = {}) {
    const errors = {}
    if (!isObject(section)) return { '': 'Must be an object.' }
    const def = defFor(section, isEducation)
    if (!def) {
        errors.template = 'Unknown template.'
        return errors
    }
    const clean = normalizeSection(section, { isEducation })
    if (!isEducation && clean.heading === '') errors.heading = 'Heading is required.'
    if (typeof section.visible !== 'boolean') errors.visible = 'Must be true or false.'
    if (section.template === 'text' && !isEducation) {
        const raw = Array.isArray(section.data) ? section.data : null
        if (!raw || raw.length !== 1 || typeof raw[0] !== 'string') errors.data = 'Rich text holds exactly one text value.'
        return errors
    }
    clean.data.forEach((item, i) => {
        for (const [path, message] of Object.entries(def.validate(item))) errors[`data.${i}${path ? `.${path}` : ''}`] = message
    })
    return errors
}

export const isSectionValid = (section, options) => Object.keys(validateSection(section, options)).length === 0

// Every skill name from the chips sections, unique ignoring case, in display order.
export function chipSkillNames(sections) {
    const seen = new Set()
    const names = []
    for (const section of sections || []) {
        if (section?.template !== 'chips') continue
        for (const item of section.data || []) {
            for (const skill of item?.skillsList || []) {
                const name = trimmed(skill?.skillName)
                const k = name.toLowerCase()
                if (name && !seen.has(k)) {
                    seen.add(k)
                    names.push(name)
                }
            }
        }
    }
    return names
}
