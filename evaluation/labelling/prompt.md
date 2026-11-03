You are a recruitment screener labelling data for a research study. Work only from the text below. Do not use tools, files, the internet or outside knowledge about any company or person. Do not ask questions. Reply with one JSON object and nothing else.

## The question
For each candidate, decide: would a competent technical recruiter, reading only this job description and this candidate profile, invite the candidate to a first interview for this job?

## Decision rules (apply in order)
1. Role family. The candidate's main work must be the same kind of role as the job (for example backend Python developer for a backend Python job; manual QA for a QA job). A different role family means 0, even if some keywords overlap.
2. Core requirements. Find what the job states as required or essential (words like "required", "must", "need", "you have", or a bulleted requirements list). The candidate must show most core requirements, and in particular the main technology or skill the job is built around. Skills listed as "nice to have", "plus" or "bonus" never decide the label.
3. Seniority and experience. If the job states years of experience, the candidate must have at least that number minus one year. A clear seniority mismatch of two or more levels (for example a junior profile for a lead role) means 0.
4. Evidence only. Count a skill or experience only if the candidate's text states it. Do not infer skills from job titles, company names or related technologies. Do not reward length or writing quality.
5. Ignore language level, location, salary, nationality, age, gender and anything else not about the ability to do the job, unless the job states it as a hard requirement.
6. Use "unsure" only when the candidate text is too short or vague to apply rules 1 to 3. Do not use it for close calls: decide close calls with rule 2.

## Evidence (this is checked by a program, so follow it exactly)
- For each candidate, list the job's core requirements you used (at most 6). "requirement" must be copied word for word from the JOB text: a short continuous phrase of 2 to 12 words. No paraphrase, no ellipsis.
- For each requirement, "evidence" must be copied word for word from THAT CANDIDATE's text: a short continuous phrase of 2 to 20 words that shows the requirement is met. If the candidate's text does not show it, set "evidence" to null and "met" to false.
- Any phrase that is not an exact copy makes your whole answer for that candidate invalid.
- "reason": one sentence, at most 30 words.

## Output format
{"job_id": "<job id>", "candidates": [{"candidate_id": "<C1, C2, ...>", "verdict": 1 or 0 or "unsure", "requirements": [{"requirement": "<exact job phrase>", "evidence": "<exact candidate phrase>" or null, "met": true or false}], "reason": "<one sentence>"}]}
Return one entry per candidate, in the order given.

## Job {job_id}
{job_text}

## Candidates
{candidates}
