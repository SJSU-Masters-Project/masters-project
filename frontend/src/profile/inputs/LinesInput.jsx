import React, { useState } from 'react'
import ui from '../../ui.module.css'

// One entry per line, for text that may contain commas (such as feature bullets).
// The raw text is kept while typing so blank lines and trailing spaces are not lost mid-edit.
export default function LinesInput({ id, value, onChange, placeholder }) {
    const [text, setText] = useState(() => value.join('\n'))
    return (
        <textarea
            id={id}
            className={ui.textarea}
            style={{ minHeight: 84 }}
            value={text}
            placeholder={placeholder}
            onChange={(e) => {
                setText(e.target.value)
                onChange(
                    e.target.value
                        .split('\n')
                        .map((l) => l.trim())
                        .filter(Boolean)
                )
            }}
        />
    )
}
