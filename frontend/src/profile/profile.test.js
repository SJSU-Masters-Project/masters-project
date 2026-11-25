import { describe, expect, it } from 'vitest'
import { deriveSkills, fromProfile, stripKeys, toBody, toEducationPatch, toForm, toSectionsPatch } from './adapters'
import { formatRange, isoToMonth, monthToIso } from './dates'
import { education, profileDoc, sections } from './fixtures'
import { safeUrl, sanitize, sanitizeForRender } from './safeHtml'
import { EDUCATION, TEMPLATES, TEMPLATE_NAMES, isSectionValid, newSection, normalizeSection, validateSection } from './templates'

const clone = (v) => JSON.parse(JSON.stringify(v))

describe('safeUrl', () => {
    it('accepts http and https', () => {
        expect(safeUrl('https://example.com/a?b=1')).toBe('https://example.com/a?b=1')
        expect(safeUrl('  http://example.com ')).toBe('http://example.com')
    })
    it.each([
        'javascript:alert(1)',
        'data:text/html,hi',
        'ftp://example.com',
        'mailto:a@b.co',
        '//example.com',
        'example.com',
        '',
        'https://',
        'https://a b.com',
    ])('rejects %s', (url) => {
        expect(safeUrl(url)).toBeNull()
    })
    it('rejects non-strings', () => {
        expect(safeUrl(null)).toBeNull()
        expect(safeUrl(5)).toBeNull()
    })
})

describe('sanitize', () => {
    it('keeps the allowed tags', () => {
        const html = '<p>a<br>b</p><ul><li><strong>x</strong></li></ul><ol><li><em>y</em></li></ol><a href="https://example.com">z</a>'
        expect(sanitize(html)).toBe(html)
    })
    it('removes scripts, handlers, styles and other tags', () => {
        const out = sanitize(
            '<p onclick="x()">hi</p><script>alert(1)</script><img src=x onerror=alert(1)><h1 style="color:red">t</h1><iframe src="https://e.com"></iframe>'
        )
        expect(out).not.toMatch(/script|onclick|onerror|<img|<h1|style|iframe/i)
        expect(out).toContain('hi')
    })
    it('drops javascript: and data: hrefs', () => {
        expect(sanitize('<a href="javascript:alert(1)">x</a>')).not.toMatch(/javascript/i)
        expect(sanitize('<a href="data:text/html,x">x</a>')).not.toMatch(/data:/i)
    })
    it('drops attributes other than href', () => {
        const out = sanitize('<a href="https://e.com" target="_self" class="c" rel="x">x</a>')
        expect(out).toBe('<a href="https://e.com">x</a>')
    })
    it('adds target and rel only for rendering', () => {
        const out = sanitizeForRender('<a href="https://e.com">x</a>')
        expect(out).toContain('target="_blank"')
        expect(out).toContain('rel="noopener noreferrer"')
        expect(sanitize('<a href="https://e.com">x</a>')).not.toContain('target')
    })
    it('treats non-strings as empty', () => {
        expect(sanitize(undefined)).toBe('')
    })
})

describe('dates', () => {
    it('converts between a month input and an ISO date', () => {
        expect(monthToIso('2026-06')).toBe('2026-06-01')
        expect(isoToMonth('2026-06-01')).toBe('2026-06')
        expect(monthToIso('')).toBeNull()
        expect(monthToIso('06/2026')).toBeNull()
        expect(isoToMonth(null)).toBe('')
    })
    it('formats ranges, with null as Present', () => {
        expect(formatRange('2026-06-01', null)).toBe('Jun 2026 – Present')
        expect(formatRange('2025-08-01', '2026-05-01')).toBe('Aug 2025 – May 2026')
        expect(formatRange(null, null)).toBe('')
    })
})

describe('normalize', () => {
    it('trims, drops empty optionals and turns empty dates into null', () => {
        expect(
            TEMPLATES.timeline.normalize({
                title: ' Dev ',
                subtitle: ' Co ',
                link: ' ',
                description: '',
                startDate: '',
                endDate: undefined,
            })
        ).toEqual({ title: 'Dev', subtitle: 'Co', startDate: null, endDate: null })
    })
    it('drops empty and duplicate techStack and features, ignoring case', () => {
        const out = TEMPLATES.cards.normalize({ title: 'T', techStack: ['React', ' react ', '', 'Node.js'], features: ['', ' '] })
        expect(out).toEqual({ title: 'T', techStack: ['React', 'Node.js'] })
    })
    it('drops chips skills without a name', () => {
        const out = TEMPLATES.chips.normalize({
            category: ' A ',
            skillsList: [
                { skillName: ' ', proficiency: 3 },
                { skillName: 'Go', proficiency: 4 },
            ],
        })
        expect(out).toEqual({ category: 'A', skillsList: [{ skillName: 'Go', proficiency: 4 }] })
    })
    it('keeps a bad proficiency as typed so validation can reject it', () => {
        expect(
            TEMPLATES.chips.normalize({ category: 'A', skillsList: [{ skillName: 'Go', proficiency: '3' }] }).skillsList[0].proficiency
        ).toBe('3')
    })
    it('normalizes education with its own field names', () => {
        expect(EDUCATION.normalize({ degree: ' MS ', institute: ' SJSU ', grade: '', link: '', startDate: '', endDate: '' })).toEqual({
            degree: 'MS',
            institute: 'SJSU',
            startDate: null,
            endDate: null,
        })
    })
})

describe('validate', () => {
    it('accepts every fixture item', () => {
        for (const section of sections) expect(validateSection(section)).toEqual({})
        expect(validateSection(education, { isEducation: true })).toEqual({})
    })
    it('has a template for every name', () => {
        for (const name of TEMPLATE_NAMES) {
            expect(TEMPLATES[name].label).toBeTruthy()
            expect(TEMPLATES[name].useCase).toBeTruthy()
            expect(typeof TEMPLATES[name].emptyItem).toBe('function')
        }
    })
    it.each([0, 6, 2.5, '3', null, undefined, NaN])('rejects proficiency %s', (proficiency) => {
        const errors = TEMPLATES.chips.validate({ category: 'A', skillsList: [{ skillName: 'Go', proficiency }] })
        expect(errors['skillsList.0.proficiency']).toBeTruthy()
    })
    it.each([1, 2, 3, 4, 5])('accepts proficiency %s', (proficiency) => {
        expect(TEMPLATES.chips.validate({ category: 'A', skillsList: [{ skillName: 'Go', proficiency }] })).toEqual({})
    })
    it('requires at least one skill in a category', () => {
        expect(TEMPLATES.chips.validate({ category: 'A', skillsList: [] }).skillsList).toBeTruthy()
    })
    it('rejects a javascript: link in every template that has one', () => {
        const bad = 'javascript:alert(1)'
        expect(TEMPLATES.cards.validate({ title: 'T', link: bad }).link).toBeTruthy()
        expect(TEMPLATES.timeline.validate({ title: 'T', subtitle: 'S', link: bad, startDate: null, endDate: null }).link).toBeTruthy()
        expect(TEMPLATES.list.validate({ title: 'T', link: bad, date: null }).link).toBeTruthy()
        expect(TEMPLATES.links.validate({ name: 'N', url: bad }).url).toBeTruthy()
        expect(EDUCATION.validate({ degree: 'D', institute: 'I', link: bad, startDate: null, endDate: null }).link).toBeTruthy()
    })
    it('rejects text data that is not exactly one string', () => {
        const base = { heading: 'About', visible: true, template: 'text' }
        expect(validateSection({ ...base, data: ['a', 'b'] }).data).toBeTruthy()
        expect(validateSection({ ...base, data: [] }).data).toBeTruthy()
        expect(validateSection({ ...base, data: [5] }).data).toBeTruthy()
        expect(validateSection({ ...base, data: ['a'] })).toEqual({})
    })
    it('reports a missing title with its path', () => {
        const errors = validateSection({ heading: 'P', visible: true, template: 'cards', data: [{ title: '  ' }] })
        expect(errors['data.0.title']).toBeTruthy()
        expect(
            validateSection({ heading: 'E', visible: true, template: 'timeline', data: [{ title: 'T', startDate: null, endDate: null }] })[
                'data.0.subtitle'
            ]
        ).toBeTruthy()
    })
    it('requires a heading and an exact date format', () => {
        expect(validateSection({ heading: ' ', visible: true, template: 'cards', data: [] }).heading).toBeTruthy()
        const bad = { heading: 'L', visible: true, template: 'list', data: [{ title: 'T', date: '03/15/2026' }] }
        expect(validateSection(bad)['data.0.date']).toBeTruthy()
        expect(TEMPLATES.list.validate({ title: 'T' }).date).toBeTruthy()
        expect(TEMPLATES.list.validate({ title: 'T', date: '' }).date).toBeTruthy()
        expect(TEMPLATES.list.validate({ title: 'T', date: '2026-02-30' }).date).toBeTruthy()
    })
    it('rejects unknown fields, unknown templates and a missing visible flag', () => {
        expect(TEMPLATES.cards.validate({ title: 'T', current: true }).current).toBe('Unknown field.')
        expect(validateSection({ heading: 'X', visible: true, template: 'grid', data: [] }).template).toBeTruthy()
        expect(validateSection({ heading: 'X', template: 'cards', data: [] }).visible).toBeTruthy()
    })
    it('treats optional fields as optional', () => {
        expect(isSectionValid({ heading: 'P', visible: true, template: 'cards', data: [{ title: 'Only a title' }] })).toBe(true)
    })
    it('creates empty sections that are valid apart from required fields', () => {
        expect(newSection('text').data).toEqual([''])
        expect(newSection('cards', 'P').data).toEqual([])
        expect(normalizeSection({ heading: ' P ', visible: true, template: 'cards', data: [] }).heading).toBe('P')
    })
})

describe('fromProfile and toBody', () => {
    it('adds client keys and strips them again', () => {
        const { sections: keyed, education: keyedEdu } = fromProfile(profileDoc)
        expect(keyed[0]._key).toBeTruthy()
        expect(keyed[0].data[0]._key).toBeTruthy()
        expect(keyed[3].data[0].skillsList[0]._key).toBeTruthy()
        expect(keyedEdu._key).toBeTruthy()
        expect(JSON.stringify(stripKeys(keyed))).not.toContain('_key')
    })
    it('gives each key a different value', () => {
        const { sections: keyed } = fromProfile(profileDoc)
        const keys = [keyed[0]._key, keyed[0].data[0]._key, keyed[0].data[1]._key, keyed[1]._key]
        expect(new Set(keys).size).toBe(keys.length)
    })
    it('returns no education when the profile has none', () => {
        expect(fromProfile({}).education).toBeNull()
        expect(fromProfile({}).sections).toEqual([])
    })
    it('round-trips all six templates and education exactly', () => {
        const { sections: keyed, education: keyedEdu } = fromProfile(clone(profileDoc))
        const body = toBody(toForm(profileDoc), keyed, keyedEdu, profileDoc, 'jordan@example.com')
        expect(body.sections).toEqual(sections)
        expect(body.education).toEqual(education)
        expect(JSON.stringify(body)).not.toContain('_key')
    })
    it('stores only the envelope keys', () => {
        const { sections: keyed } = fromProfile(profileDoc)
        for (const s of toBody(toForm(profileDoc), keyed, null, profileDoc, 'a@b.co').sections) {
            expect(Object.keys(s).sort()).toEqual(['data', 'heading', 'template', 'visible'])
        }
    })
    it('derives career.skills from every chips section, unique ignoring case', () => {
        const { sections: keyed } = fromProfile(profileDoc)
        const body = toBody(toForm(profileDoc), keyed, null, profileDoc, 'a@b.co')
        expect(body.career.skills).toEqual(['React', 'CSS', 'Python'])
        expect(deriveSkills(sections)).toEqual(['React', 'CSS', 'Python'])
    })
    it('leaves education out of the body when there is none, and keeps fields the form does not edit', () => {
        const body = toBody(toForm(profileDoc), [], null, profileDoc, 'a@b.co')
        expect('education' in body).toBe(false)
        expect(body.sections).toEqual([])
        expect(body.career.skills).toEqual([])
        expect(body.career.experience).toEqual(profileDoc.career.experience)
    })
    it('builds patches for sections and education', () => {
        const { sections: keyed, education: keyedEdu } = fromProfile(profileDoc)
        const patch = toSectionsPatch(keyed, profileDoc)
        expect(Object.keys(patch).sort()).toEqual(['career', 'sections'])
        expect(patch.career.skills).toEqual(['React', 'CSS', 'Python'])
        expect(patch.career.headline).toBe('Student')
        expect(toEducationPatch(keyedEdu)).toEqual({ education: education })
    })
    it('sanitizes rich text on the way out', () => {
        const dirty = [{ heading: 'A', visible: true, template: 'text', data: ['<p onclick="x()">hi</p><script>alert(1)</script>'] }]
        expect(toBody(toForm(profileDoc), dirty, null, profileDoc, 'a@b.co').sections[0].data).toEqual(['<p>hi</p>'])
    })
})
