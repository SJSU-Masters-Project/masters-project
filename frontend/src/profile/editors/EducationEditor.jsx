import React from 'react'
import TimelineEditor from './TimelineEditor'

// The top-level education section: the timeline editor with degree / institute / grade fields.
export default function EducationEditor(props) {
    return <TimelineEditor {...props} education />
}
