// A profile document with every template once, plus education. Used by the tests.

export const education = {
    heading: 'Education',
    visible: true,
    template: 'timeline',
    data: [
        {
            degree: 'MS Software Engineering',
            institute: 'San Jose State University',
            grade: '3.9 GPA',
            link: 'https://www.sjsu.edu',
            startDate: '2025-08-01',
            endDate: null,
        },
        { degree: 'BTech Computer Science', institute: 'Example Institute', startDate: '2021-08-01', endDate: '2025-05-01' },
    ],
}

export const sections = [
    {
        heading: 'Projects',
        visible: true,
        template: 'cards',
        data: [
            {
                title: 'Careers portal',
                purpose: 'A job portal for students.',
                link: 'https://example.com/careers',
                techStack: ['React', 'Django'],
                features: ['Job search', 'Profiles'],
            },
            { title: 'Bare card' },
        ],
    },
    {
        heading: 'Experience',
        visible: true,
        template: 'timeline',
        data: [
            {
                title: 'Software Engineering Intern',
                subtitle: 'Northstar Labs',
                link: 'https://example.com/northstar',
                description: 'Built dashboards.',
                startDate: '2026-06-01',
                endDate: null,
            },
            { title: 'Tutor', subtitle: 'SJSU', startDate: null, endDate: null },
        ],
    },
    {
        heading: 'Certifications',
        visible: false,
        template: 'list',
        data: [
            {
                title: 'AWS Cloud Practitioner',
                subtitle: 'Amazon Web Services',
                link: 'https://example.com/verify',
                date: '2026-03-15',
                description: 'Foundational certification.',
            },
            { title: 'Dean’s list', date: null },
        ],
    },
    {
        heading: 'Skills',
        visible: true,
        template: 'chips',
        data: [
            {
                category: 'Frontend',
                skillsList: [
                    { skillName: 'React', proficiency: 4 },
                    { skillName: 'CSS', proficiency: 3 },
                ],
            },
            {
                category: 'Backend',
                skillsList: [
                    { skillName: 'Python', proficiency: 5 },
                    { skillName: 'react', proficiency: 2 },
                ],
            },
        ],
    },
    {
        heading: 'Links',
        visible: true,
        template: 'links',
        data: [
            { name: 'GitHub', url: 'https://github.com/example', description: 'My code.' },
            { name: 'Blog', url: 'https://example.com/blog' },
        ],
    },
    {
        heading: 'About me',
        visible: true,
        template: 'text',
        data: ['<p>Hello <strong>there</strong>, see <a href="https://example.com">my site</a>.</p>'],
    },
]

export const profileDoc = {
    id: 'p1',
    visibility: 'private',
    personal: { fullName: 'Jordan Lee', email: 'jordan@example.com', phone: '555-0100', location: 'San Jose, CA' },
    academic: [],
    certifications: [],
    achievements: [],
    career: { headline: 'Student', summary: 'Hi', skills: [], experience: [{ company: 'Old Co', title: 'Dev' }] },
    jobPreferences: { targetRoles: ['SWE'], employmentTypes: ['full_time'], workModes: ['remote'] },
    education,
    sections,
}
