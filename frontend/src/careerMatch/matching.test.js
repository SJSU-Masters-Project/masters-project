import { describe, expect, it } from 'vitest'
import { analyzeJob, careerPlan, completeness, growthAreas, isSuggested, profileSkillSet, rankJobs, whyLine } from './matching'

const job = (id, skills) => ({
    id,
    title: `Job ${id}`,
    skills: skills.map(([name, required]) => ({ name, required })),
})

const skillSet = (names) => profileSkillSet(names)

describe('analyzeJob', () => {
    it('computes alignment as the share of required skills on the profile, case-insensitively', () => {
        const a = analyzeJob(
            job(1, [
                ['React', true],
                ['AWS', true],
                ['Figma', false],
            ]),
            skillSet(['react', 'python'])
        )
        expect(a.required).toEqual(['React', 'AWS'])
        expect(a.matched).toEqual(['React'])
        expect(a.missing).toEqual(['AWS'])
        expect(a.alignment).toBe(50)
    })
    it('rounds to the nearest percent', () => {
        const a = analyzeJob(
            job(1, [
                ['A', true],
                ['B', true],
                ['C', true],
            ]),
            skillSet(['a', 'b'])
        )
        expect(a.alignment).toBe(67)
    })
    it('gives 100 when every required skill is present and ignores optional skills', () => {
        const a = analyzeJob(
            job(1, [
                ['A', true],
                ['B', false],
            ]),
            skillSet(['a'])
        )
        expect(a.alignment).toBe(100)
    })
    it('has no alignment when the job lists no required skills', () => {
        expect(analyzeJob(job(1, [['A', false]]), skillSet(['a'])).alignment).toBeNull()
    })
})

describe('rankJobs and isSuggested', () => {
    const jobs = [
        job(1, [
            ['React', true],
            ['AWS', true],
        ]),
        job(2, [['Python', true]]),
        job(3, [
            ['Go', true],
            ['Rust', true],
        ]),
        job(4, [['Optional', false]]),
    ]
    it('sorts by alignment, highest first, and puts no-requirement jobs last', () => {
        const ranked = rankJobs(jobs, ['React', 'AWS'])
        // job 1 (React+AWS) 100, job 3 (Go+Rust) 0, job 2 (Python) 0, job 4 (no required) last.
        expect(ranked.map((j) => j.id)).toEqual([1, 2, 3, 4])
        expect(ranked[0].alignment).toBe(100)
        expect(ranked[1].alignment).toBe(0)
        expect(ranked.at(-1).alignment).toBeNull()
    })
    it('marks a job suggested only when a required skill matches', () => {
        const [j1, j2, j3] = rankJobs(jobs, ['React']).filter((j) => [1, 2, 3].includes(j.id))
        void [j1, j2, j3]
        expect(isSuggested(analyzeJob(jobs[0], skillSet(['React'])))).toBe(true)
        expect(isSuggested(analyzeJob(jobs[2], skillSet(['React'])))).toBe(false)
    })
})

describe('whyLine', () => {
    it('names the matched skills and never repeats one fixed string', () => {
        const base = skillSet(['react', 'sql', 'git'])
        expect(whyLine(analyzeJob(job(1, [['React', true]]), base))).toContain('React')
        expect(
            whyLine(
                analyzeJob(
                    job(1, [
                        ['React', true],
                        ['SQL', true],
                    ]),
                    base
                )
            )
        ).toBe('Your React and SQL match required skills for this role.')
        expect(
            whyLine(
                analyzeJob(
                    job(1, [
                        ['React', true],
                        ['SQL', true],
                        ['Git', true],
                    ]),
                    base
                )
            )
        ).toContain('React, SQL, Git')
        expect(whyLine(analyzeJob(job(1, [['Rust', true]]), base))).toMatch(/add matching skills/)
    })
})

describe('completeness', () => {
    const full = {
        personal: { fullName: 'Jordan' },
        career: { headline: 'Student', resumeId: 'r1' },
        education: { data: [{ degree: 'MS' }] },
        sections: [
            { template: 'chips', data: [{ category: 'c', skillsList: [{ skillName: 'x', proficiency: 3 }] }] },
            { template: 'cards', data: [{ title: 'p' }] },
        ],
    }
    it('is 100% when all six are filled', () => {
        expect(completeness(full).percent).toBe(100)
        expect(completeness(full).firstMissing).toBeNull()
    })
    it('counts each sixth and names the first missing item', () => {
        const p = { ...full, career: { headline: 'Student', resumeId: 'r1' }, personal: {} }
        expect(completeness(p).percent).toBe(83)
        expect(completeness(p).firstMissing).toBe('your full name')
    })
    it('needs items, not just a section, for education, chips and cards', () => {
        const p = { personal: {}, career: {}, education: { data: [] }, sections: [{ template: 'chips', data: [] }] }
        expect(completeness(p).percent).toBe(0)
        expect(completeness(p).firstMissing).toBe('your full name')
    })
    it('handles a missing profile', () => {
        expect(completeness(null).percent).toBe(0)
    })
})

describe('growthAreas and careerPlan', () => {
    const jobs = [
        job(1, [
            ['React', true],
            ['AWS', true],
        ]),
        job(2, [
            ['AWS', true],
            ['Docker', true],
        ]),
        job(3, [['Go', true]]),
    ]
    it('lists distinct missing required skills across suggested jobs only', () => {
        const ranked = rankJobs(jobs, ['React', 'AWS'])
        // job 3 (Go) is not suggested; its missing Go is excluded.
        expect(growthAreas(ranked)).toEqual(['Docker'])
    })
    it('builds plan steps from real growth areas and is empty when there are none', () => {
        const ranked = rankJobs(jobs, ['React'])
        const plan = careerPlan(ranked)
        expect(plan[0]).toMatch(/Build a project using/)
        expect(plan.some((s) => s.includes('Practice interview questions'))).toBe(true)
        expect(plan).toContain('Strengthen your portfolio')
        expect(careerPlan(rankJobs(jobs, ['React', 'AWS', 'Docker']))).toEqual([])
    })
})
