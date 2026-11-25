// Prof. Dhar's profile section templates, as stored. Documentation only: nothing is exported at runtime.
//
// Every custom section is one envelope. The template decides the shape of the items in `data`.
// Dates are ISO-8601 date strings (YYYY-MM-DD) or null. A null `endDate` means "Present".
// Stored data never carries ids or ordering fields; array position is the display order.

/**
 * @typedef {'cards' | 'timeline' | 'list' | 'chips' | 'links' | 'text'} TemplateName
 */

/**
 * The common envelope.
 * @template T
 * @typedef {object} SectionEnvelope
 * @property {string} heading
 * @property {boolean} visible
 * @property {TemplateName} template
 * @property {T[]} data
 */

/**
 * "cards": projects, portfolio highlights and accomplishments.
 * @typedef {object} CardItem
 * @property {string} title Project or card title.
 * @property {string} [purpose] Brief description or summary.
 * @property {string} [link] External URL (http or https).
 * @property {string[]} [techStack] For example ["React", "Node.js"].
 * @property {string[]} [features] Bullet points.
 */

/**
 * "timeline": chronological records such as work experience.
 * @typedef {object} TimelineItem
 * @property {string} title Position or role title.
 * @property {string} subtitle Company or organization.
 * @property {string} [link] Company or reference URL (http or https).
 * @property {string} [description] Responsibilities and achievements.
 * @property {string | null} startDate
 * @property {string | null} endDate Null means "Present".
 */

/**
 * The top-level "education" section uses the timeline template with these fields.
 * @typedef {object} EducationItem
 * @property {string} degree
 * @property {string} institute
 * @property {string} [grade]
 * @property {string} [link] http or https.
 * @property {string | null} startDate
 * @property {string | null} endDate Null means "Present".
 */

/**
 * "list": certifications, publications and awards.
 * @typedef {object} ListItem
 * @property {string} title Credential or publication title.
 * @property {string} [subtitle] Issuing organization or publisher.
 * @property {string} [link] Verification link (http or https).
 * @property {string | null} date
 * @property {string} [description]
 */

/**
 * @typedef {object} ChipSkill
 * @property {string} skillName
 * @property {number} proficiency A whole number from 1 to 5.
 */

/**
 * "chips": categorized skills with proficiency scores.
 * @typedef {object} ChipsItem
 * @property {string} category For example "Frontend".
 * @property {ChipSkill[]} skillsList At least one entry.
 */

/**
 * "links": curated web links and personal resources.
 * @typedef {object} LinkItem
 * @property {string} name Display label.
 * @property {string} url Destination (http or https).
 * @property {string} [description]
 */

/**
 * "text": freeform rich text. `data` holds exactly one HTML/text string.
 * @typedef {string} TextItem
 */

/** @typedef {SectionEnvelope<CardItem>} CardsSection */
/** @typedef {SectionEnvelope<TimelineItem>} TimelineSection */
/** @typedef {SectionEnvelope<ListItem>} ListSection */
/** @typedef {SectionEnvelope<ChipsItem>} ChipsSection */
/** @typedef {SectionEnvelope<LinkItem>} LinksSection */
/** @typedef {SectionEnvelope<TextItem>} TextSection */

/**
 * The top-level education envelope: always the timeline template, heading "Education".
 * @typedef {SectionEnvelope<EducationItem>} EducationSection
 */

/**
 * Any custom section. Edited copies carry a client-only `_key` on the envelope and on each item;
 * it is stripped before saving.
 * @typedef {CardsSection | TimelineSection | ListSection | ChipsSection | LinksSection | TextSection} Section
 */

export {}
