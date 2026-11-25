import React from 'react'
import ChipsView from './ChipsView'
import CardsView from './CardsView'
import LinksView from './LinksView'
import ListView from './ListView'
import TextView from './TextView'
import TimelineView from './TimelineView'

const VIEWS = { cards: CardsView, timeline: TimelineView, list: ListView, chips: ChipsView, links: LinksView, text: TextView }

// Picks the read-only view for a section's template. `education` is the top-level education section.
export default function SectionView({ section, education = false }) {
    const View = VIEWS[section.template]
    const items = section.data || []
    if (!View || items.length === 0) return null
    return education ? <TimelineView items={items} education /> : <View items={items} />
}
