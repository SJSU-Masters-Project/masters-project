import React from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it } from 'vitest'
import { education, sections } from '../fixtures'
import SectionView from './SectionView'

const html = (section, props) => renderToStaticMarkup(<SectionView section={section} {...props} />)
const byTemplate = (name) => sections.find((s) => s.template === name)

describe('section views', () => {
    it('renders cards with an accessible external link, tech stack and features', () => {
        const out = html(byTemplate('cards'))
        expect(out).toContain('Careers portal')
        expect(out).toContain('aria-label="Open Careers portal"')
        expect(out).toContain('target="_blank"')
        expect(out).toContain('rel="noopener noreferrer"')
        expect(out).toContain('Django')
        expect(out).toContain('Job search')
    })
    it('leaves out empty optional fields and never shows a placeholder dash', () => {
        const out = html({ heading: 'P', visible: true, template: 'cards', data: [{ title: 'Bare card' }] })
        expect(out).toContain('Bare card')
        expect(out).not.toContain('<a ')
        expect(out).not.toContain('<ul')
        expect(out).not.toMatch(/>\s*[—–-]\s*</)
    })
    it('renders a timeline with Present for a null end date', () => {
        const out = html(byTemplate('timeline'))
        expect(out).toContain('Jun 2026 – Present')
        expect(out).toContain('Northstar Labs')
    })
    it('renders a timeline entry with no dates without a date line', () => {
        const out = html({
            heading: 'T',
            visible: true,
            template: 'timeline',
            data: [{ title: 'Tutor', subtitle: 'SJSU', startDate: null, endDate: null }],
        })
        expect(out).not.toContain('Present')
    })
    it('renders education with degree, institute and grade', () => {
        const out = html(education, { education: true })
        expect(out).toContain('MS Software Engineering')
        expect(out).toContain('San Jose State University')
        expect(out).toContain('Grade: 3.9 GPA')
        expect(out).toContain('Aug 2025 – Present')
    })
    it('renders a list with subtitle, date and a Verify link', () => {
        const out = html(byTemplate('list'))
        expect(out).toContain('Amazon Web Services · Mar 15, 2026')
        expect(out).toContain('Verify')
    })
    it('renders chips with a screen reader score and dots', () => {
        const out = html(byTemplate('chips'))
        expect(out).toContain('Frontend')
        expect(out).toContain('4 of 5')
        expect(out).toContain('5 of 5')
    })
    it('renders links and refuses an unsafe url as a link', () => {
        const out = html(byTemplate('links'))
        expect(out).toContain('href="https://github.com/example"')
        const bad = html({ heading: 'L', visible: true, template: 'links', data: [{ name: 'Bad', url: 'javascript:alert(1)' }] })
        expect(bad).not.toContain('href=')
    })
    it('sanitizes rich text again on render', () => {
        const out = html({
            heading: 'A',
            visible: true,
            template: 'text',
            data: ['<p>ok</p><script>alert(1)</script><a href="javascript:x">bad</a>'],
        })
        expect(out).toContain('<p>ok</p>')
        expect(out).not.toMatch(/script|javascript/i)
    })
    it('renders nothing for a section without items', () => {
        expect(html({ heading: 'E', visible: true, template: 'cards', data: [] })).toBe('')
    })
})
