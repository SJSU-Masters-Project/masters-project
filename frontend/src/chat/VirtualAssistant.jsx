import React, { useEffect, useRef, useState } from 'react'
import { MessageCircle, Send, Sparkles, X } from 'lucide-react'
import styles from './VirtualAssistant.module.css'

const prompts = ['How can I improve my resume?', 'How do I find roles that match my skills?', 'Help me prepare for an interview.']

// The chat service is not part of this repository yet. Keep the composer available for
// design review, but do not imply a message has been sent or invent assistant replies.
export default function VirtualAssistant() {
    const [open, setOpen] = useState(false)
    const [draft, setDraft] = useState('')
    const closeRef = useRef(null)
    const triggerRef = useRef(null)
    const inputRef = useRef(null)

    useEffect(() => {
        if (!open) return undefined
        closeRef.current?.focus()
        const onKeyDown = (event) => {
            if (event.key === 'Escape') {
                setOpen(false)
                triggerRef.current?.focus()
            }
        }
        document.addEventListener('keydown', onKeyDown)
        return () => document.removeEventListener('keydown', onKeyDown)
    }, [open])

    const close = () => {
        setOpen(false)
        triggerRef.current?.focus()
    }

    return (
        <div className={styles.assistant}>
            {open && (
                <section className={styles.panel} aria-label="Virtual assistant" aria-describedby="assistant-status">
                    <header className={styles.header}>
                        <span className={styles.mark}>
                            <Sparkles size={19} aria-hidden="true" />
                        </span>
                        <div className={styles.heading}>
                            <h2>Virtual assistant</h2>
                            <p>Career support, in one place</p>
                        </div>
                        <button ref={closeRef} type="button" className={styles.close} onClick={close} aria-label="Close virtual assistant">
                            <X size={20} aria-hidden="true" />
                        </button>
                    </header>
                    <div className={styles.body}>
                        <div className={styles.intro}>
                            <span className={styles.introIcon}>
                                <MessageCircle size={20} aria-hidden="true" />
                            </span>
                            <h3>What would you like to work on?</h3>
                            <p>Get started with a question about your career journey.</p>
                        </div>
                        <div className={styles.suggestions} aria-label="Suggested questions">
                            {prompts.map((prompt) => (
                                <button
                                    key={prompt}
                                    type="button"
                                    onClick={() => {
                                        setDraft(prompt)
                                        inputRef.current?.focus()
                                    }}
                                >
                                    {prompt}
                                </button>
                            ))}
                        </div>
                    </div>
                    <div className={styles.composer}>
                        <p id="assistant-status" className={styles.status}>
                            Chat is not connected yet. Messages cannot be sent.
                        </p>
                        <label className={styles.label} htmlFor="assistant-draft">
                            Your message
                        </label>
                        <div className={styles.inputRow}>
                            <textarea
                                ref={inputRef}
                                id="assistant-draft"
                                rows="2"
                                maxLength={2000}
                                value={draft}
                                onChange={(event) => setDraft(event.target.value)}
                                placeholder="Ask a career question…"
                            />
                            <button type="button" disabled aria-label="Send message (chat not connected)">
                                <Send size={18} aria-hidden="true" />
                            </button>
                        </div>
                    </div>
                </section>
            )}
            <button
                ref={triggerRef}
                type="button"
                className={styles.launcher}
                aria-expanded={open}
                onClick={() => setOpen((value) => !value)}
            >
                <MessageCircle size={19} aria-hidden="true" /> <span>Virtual assistant</span>
            </button>
        </div>
    )
}
