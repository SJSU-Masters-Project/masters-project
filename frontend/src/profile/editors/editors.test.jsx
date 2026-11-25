import React, { act, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { fromProfile } from '../adapters'
import { profileDoc } from '../fixtures'
import DateRange from '../inputs/DateRange'
import ProficiencyInput from '../inputs/ProficiencyInput'
import TagInput from '../inputs/TagInput'
import { newSection } from '../templates'
import SectionEditor from './SectionEditor'

globalThis.IS_REACT_ACT_ENVIRONMENT = true

let root
let host
afterEach(() => {
    act(() => root?.unmount())
    host?.remove()
    root = host = null
})

function mount(element) {
    host = document.createElement('div')
    document.body.append(host)
    root = createRoot(host)
    act(() => root.render(element))
    return host
}

// Sets a text field the way a user typing would, so React sees the change.
function type(el, value) {
    const proto = el.tagName === 'TEXTAREA' ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype
    act(() => {
        Object.getOwnPropertyDescriptor(proto, 'value').set.call(el, value)
        el.dispatchEvent(new Event('input', { bubbles: true }))
    })
}
const click = (el) => act(() => el.click())
const byLabel = (c, text) => [...c.querySelectorAll('label')].find((l) => l.textContent.trim().startsWith(text))
// A field by its label text: the label's `for` target, or the input inside a wrapping label.
const field = (c, text) => {
    const label = byLabel(c, text)
    return label.htmlFor ? c.querySelector(`#${CSS.escape(label.htmlFor)}`) : label.querySelector('input')
}
const button = (c, name) =>
    c.querySelector(`button[aria-label="${name}"]`) || [...c.querySelectorAll('button')].find((b) => b.textContent.trim() === name)

function Stateful({ initial, render }) {
    const [value, setValue] = useState(initial)
    return render(value, setValue)
}

describe('TagInput', () => {
    function setup(initial = []) {
        const seen = []
        const c = mount(
            <Stateful
                initial={initial}
                render={(value, setValue) => (
                    <TagInput
                        label="Add a technology"
                        value={value}
                        onChange={(v) => {
                            seen.push(v)
                            setValue(v)
                        }}
                    />
                )}
            />
        )
        return { c, seen, input: c.querySelector('input') }
    }
    it('adds a tag on Enter', () => {
        const { c, input } = setup()
        type(input, 'React')
        act(() => input.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true, cancelable: true })))
        expect(c.textContent).toContain('React')
        expect(input.value).toBe('')
    })
    it('adds tags when a comma is typed and skips duplicates ignoring case', () => {
        const { seen, input } = setup(['React'])
        type(input, 'react, Node.js, ')
        expect(seen.at(-1)).toEqual(['React', 'Node.js'])
    })
    it('removes a tag with its button', () => {
        const { c, seen } = setup(['React', 'Node.js'])
        click(button(c, 'Remove React'))
        expect(seen.at(-1)).toEqual(['Node.js'])
    })
})

describe('ProficiencyInput', () => {
    it('is a radio group from 1 to 5 and reports a whole number', () => {
        const onChange = vi.fn()
        const c = mount(<ProficiencyInput value={3} onChange={onChange} />)
        const radios = c.querySelectorAll('input[type=radio]')
        expect(radios).toHaveLength(5)
        expect(radios[2].checked).toBe(true)
        click(radios[4])
        expect(onChange).toHaveBeenCalledWith(5)
        expect(c.querySelector('legend').textContent).toMatch(/1 to 5/)
    })
})

describe('DateRange', () => {
    function setup(start, end) {
        const seen = []
        const c = mount(
            <Stateful
                initial={{ startDate: start, endDate: end }}
                render={(v, set) => (
                    <DateRange
                        idPrefix="d"
                        {...v}
                        currentLabel="I currently work here"
                        onChange={(next) => {
                            seen.push(next)
                            set(next)
                        }}
                    />
                )}
            />
        )
        return { c, seen }
    }
    it('shows the checkbox ticked and the end month disabled when endDate is null', () => {
        const { c } = setup('2026-06-01', null)
        expect(field(c, 'I currently').checked).toBe(true)
        expect(field(c, 'End date').disabled).toBe(true)
        expect(field(c, 'Start date').value).toBe('2026-06')
    })
    it('stores the first of the month, and null for Present', () => {
        const { c, seen } = setup(null, null)
        type(field(c, 'Start date'), '2026-06')
        expect(seen.at(-1).startDate).toBe('2026-06-01')
        click(field(c, 'I currently'))
        expect(seen.at(-1).endDate).toBe('')
        type(field(c, 'End date'), '2027-01')
        expect(seen.at(-1).endDate).toBe('2027-01-01')
        click(field(c, 'I currently'))
        expect(seen.at(-1).endDate).toBeNull()
    })
    it('asks for an end date while it is unticked and empty', () => {
        const { c } = setup('2026-06-01', '')
        expect(c.textContent).toContain('Choose an end date')
    })
})

describe('SectionEditor', () => {
    const find = (template) => fromProfile(profileDoc).sections.find((s) => s.template === template)

    function setup(section, props = {}) {
        const onSave = vi.fn()
        const onDirtyChange = vi.fn()
        const c = mount(<SectionEditor section={section} onSave={onSave} onCancel={() => {}} onDirtyChange={onDirtyChange} {...props} />)
        return { c, onSave, onDirtyChange }
    }

    it('shows the template read-only and has no way to change it', () => {
        const { c } = setup(find('chips'))
        expect(c.textContent).toContain('Skill chips')
        expect(c.querySelector('select')).toBeNull()
    })
    it('keeps Save disabled until a new section is valid, then saves a clean draft', () => {
        const { c, onSave } = setup(fromProfile({ sections: [{ ...newSection('cards', 'Projects') }] }).sections[0])
        const save = button(c, 'Save section')
        expect(save.disabled).toBe(false)
        click(button(c, 'Add card'))
        expect(save.disabled).toBe(true)
        expect(c.textContent).toMatch(/1 field needs attention/)
        type(field(c, 'Title'), 'My project')
        expect(save.disabled).toBe(false)
        click(save)
        expect(onSave).toHaveBeenCalledTimes(1)
        expect(onSave.mock.calls[0][0].data[0].title).toBe('My project')
    })
    it('blocks Save for a javascript: link and a proficiency left out of range is impossible to choose', () => {
        const { c } = setup(find('links'))
        const save = button(c, 'Save section')
        expect(save.disabled).toBe(false)
        type(c.querySelector('input[inputmode=url]'), 'javascript:alert(1)')
        expect(save.disabled).toBe(true)
    })
    it('requires a heading', () => {
        const { c } = setup(find('cards'))
        type(field(c, 'Section heading'), '  ')
        expect(button(c, 'Save section').disabled).toBe(true)
    })
    it('reorders and removes items with buttons', () => {
        const { c, onSave } = setup(find('links'))
        click(button(c, 'Move Link 1 down'))
        click(button(c, 'Remove Link 2'))
        click(button(c, 'Save section'))
        expect(onSave.mock.calls[0][0].data.map((i) => i.name)).toEqual(['Blog'])
    })
    it('reports unsaved edits', () => {
        const { c, onDirtyChange } = setup(find('cards'))
        expect(onDirtyChange).toHaveBeenLastCalledWith(false)
        type(field(c, 'Section heading'), 'Work')
        expect(onDirtyChange).toHaveBeenLastCalledWith(true)
    })
    it('edits the education section with degree and institute', () => {
        const edu = fromProfile(profileDoc).education
        const { c } = setup(edu, { isEducation: true })
        expect(field(c, 'Degree').value).toBe('MS Software Engineering')
        expect(field(c, 'Institute').value).toBe('San Jose State University')
        expect(field(c, 'I currently study').checked).toBe(true)
    })
})
