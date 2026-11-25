import React, { useEffect, useRef, useState } from 'react'
import Link from '@tiptap/extension-link'
import { EditorContent, useEditor, useEditorState } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import { Bold, Italic, Link2, List, ListOrdered, Unlink } from 'lucide-react'
import ui from '../../ui.module.css'
import { safeUrl, sanitize } from '../safeHtml'
import styles from './editors.module.css'

function ToolButton({ label, active, onClick, disabled, children }) {
    return (
        <button
            type="button"
            className={`${styles.tool} ${active ? styles.toolOn : ''}`}
            onClick={onClick}
            disabled={disabled}
            aria-label={label}
            aria-pressed={active}
            title={label}
        >
            {children}
        </button>
    )
}

// Bold, italic, bullet and numbered lists, and links: nothing else. Output is sanitized before it leaves.
function RichTextEditor({ id, value, onChange }) {
    const [linkOpen, setLinkOpen] = useState(false)
    const [url, setUrl] = useState('')
    const [urlError, setUrlError] = useState(null)
    const last = useRef(value)

    const editor = useEditor({
        extensions: [
            StarterKit.configure({
                blockquote: false,
                code: false,
                codeBlock: false,
                heading: false,
                horizontalRule: false,
                strike: false,
                underline: false,
                link: false,
            }),
            Link.configure({
                openOnClick: false,
                autolink: false,
                linkOnPaste: false,
                protocols: ['http', 'https'],
                defaultProtocol: 'https',
            }),
        ],
        content: value,
        editorProps: { attributes: { id, role: 'textbox', 'aria-multiline': 'true', 'aria-label': 'Rich text' } },
        onUpdate: ({ editor: ed }) => {
            const html = ed.isEmpty ? '' : sanitize(ed.getHTML())
            last.current = html
            onChange(html)
        },
    })

    // Follow outside changes to the value (for example a reset) without fighting the user's typing.
    useEffect(() => {
        if (editor && value !== last.current) {
            last.current = value
            editor.commands.setContent(value, { emitUpdate: false })
        }
    }, [editor, value])

    const state = useEditorState({
        editor,
        selector: ({ editor: ed }) => ({
            bold: ed?.isActive('bold') ?? false,
            italic: ed?.isActive('italic') ?? false,
            bullet: ed?.isActive('bulletList') ?? false,
            ordered: ed?.isActive('orderedList') ?? false,
            link: ed?.isActive('link') ?? false,
        }),
    })

    if (!editor) return null

    const openLink = () => {
        setUrl(editor.getAttributes('link').href || '')
        setUrlError(null)
        setLinkOpen(true)
    }
    const applyLink = () => {
        const safe = safeUrl(url)
        if (!safe) {
            setUrlError('Enter a link that starts with http:// or https://.')
            return
        }
        editor.chain().focus().extendMarkRange('link').setLink({ href: safe }).run()
        setLinkOpen(false)
    }

    return (
        <div className={styles.rte}>
            <div className={styles.toolbar} role="toolbar" aria-label="Text formatting">
                <ToolButton label="Bold" active={state.bold} onClick={() => editor.chain().focus().toggleBold().run()}>
                    <Bold size={16} aria-hidden="true" />
                </ToolButton>
                <ToolButton label="Italic" active={state.italic} onClick={() => editor.chain().focus().toggleItalic().run()}>
                    <Italic size={16} aria-hidden="true" />
                </ToolButton>
                <ToolButton label="Bulleted list" active={state.bullet} onClick={() => editor.chain().focus().toggleBulletList().run()}>
                    <List size={16} aria-hidden="true" />
                </ToolButton>
                <ToolButton label="Numbered list" active={state.ordered} onClick={() => editor.chain().focus().toggleOrderedList().run()}>
                    <ListOrdered size={16} aria-hidden="true" />
                </ToolButton>
                <ToolButton label="Link" active={state.link || linkOpen} onClick={openLink}>
                    <Link2 size={16} aria-hidden="true" />
                </ToolButton>
                <ToolButton
                    label="Remove link"
                    active={false}
                    disabled={!state.link}
                    onClick={() => editor.chain().focus().extendMarkRange('link').unsetLink().run()}
                >
                    <Unlink size={16} aria-hidden="true" />
                </ToolButton>
            </div>
            {linkOpen && (
                <div className={styles.linkBar}>
                    <input
                        className={ui.input}
                        value={url}
                        onChange={(e) => setUrl(e.target.value)}
                        onKeyDown={(e) => {
                            if (e.key === 'Enter') {
                                e.preventDefault()
                                applyLink()
                            } else if (e.key === 'Escape') {
                                e.stopPropagation()
                                setLinkOpen(false)
                            }
                        }}
                        placeholder="https://example.com"
                        inputMode="url"
                        aria-label="Link address"
                        aria-invalid={Boolean(urlError)}
                        autoFocus
                    />
                    <button type="button" className="btn contained small" onClick={applyLink}>
                        Apply
                    </button>
                    <button type="button" className="btn outlined small" onClick={() => setLinkOpen(false)}>
                        Cancel
                    </button>
                    {urlError && <span className={ui.fieldError}>{urlError}</span>}
                </div>
            )}
            <EditorContent editor={editor} className={styles.surface} />
        </div>
    )
}

// The rich text template: its data is exactly one string, so `items` is [html].
export default function TextEditor({ items, onChange, idPrefix }) {
    return <RichTextEditor id={`${idPrefix}-rte`} value={items[0] || ''} onChange={(html) => onChange([html])} />
}
