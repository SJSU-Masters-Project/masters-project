import React, { act } from 'react'
import { createRoot } from 'react-dom/client'
import { afterEach, beforeEach, expect, it } from 'vitest'
import VirtualAssistant from './VirtualAssistant'

let container
let root
beforeEach(() => {
    globalThis.IS_REACT_ACT_ENVIRONMENT = true
    container = document.createElement('div')
    document.body.appendChild(container)
    root = createRoot(container)
    act(() => root.render(<VirtualAssistant />))
})
afterEach(() => {
    act(() => root.unmount())
    container.remove()
})

it('opens, fills a suggested question, and closes without sending', () => {
    const launcher = container.querySelector('button')
    act(() => launcher.click())
    expect(launcher.getAttribute('aria-expanded')).toBe('true')
    expect(container.textContent).toContain('Messages cannot be sent')
    expect(container.querySelector('button[aria-label^="Send message"]').disabled).toBe(true)
    const suggestion = [...container.querySelectorAll('button')].find((button) => button.textContent.includes('improve my resume'))
    act(() => suggestion.click())
    expect(container.querySelector('textarea').value).toBe('How can I improve my resume?')
    act(() => document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true })))
    expect(container.querySelector('section')).toBeNull()
    expect(document.activeElement).toBe(launcher)
})
