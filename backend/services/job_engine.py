"""AI job-content generation.

Given a job's structured fields (title, skills, experience, ...), produce a full
posting: description, responsibilities, requirements, preferred qualifications,
benefits, hiring timeline, interview plan, suggested skill assessment, and
technical + HR questions.

Offline-first: a deterministic generator always produces sensible content from
the structured fields; the AI layer refines/expands it when a key is configured.
Never raises.
"""
from __future__ import annotations

import logging
from typing import Dict, List

from services.ai_client import chat, extract_json

logger = logging.getLogger("hiringbuddy.job_engine")

_GENERATED_KEYS = [
    "description", "responsibilities", "requirements", "preferred_qualifications",
    "benefits", "hiring_timeline", "interview_plan", "skill_assessment",
    "technical_questions", "hr_questions",
]


def _fmt_exp(job) -> str:
    lo = job.experience_min or 0
    hi = job.experience_max
    if hi and hi > lo:
        return f"{lo:g}-{hi:g} years"
    return f"{lo:g}+ years" if lo else "entry level"


def _deterministic(job) -> Dict:
    """Full, sensible posting derived purely from structured fields."""
    title = job.title or "the role"
    company = job.company or "our company"
    mode = (job.work_mode or "").capitalize()
    loc = job.location or ("Remote" if job.work_mode == "remote" else "our office")
    req = [s for s in (job.required_skills or []) if s]
    pref = [s for s in (job.preferred_skills or []) if s]
    exp = _fmt_exp(job)

    skills_phrase = ", ".join(req[:6]) if req else "modern tooling"

    description = (
        f"{company} is hiring a {title}"
        f"{f' ({mode})' if mode else ''}"
        f"{f' based in {loc}' if loc else ''}. "
        f"You will work with {skills_phrase} to build and ship high-quality products. "
        f"We're looking for someone with {exp} of experience who cares about craft, "
        f"collaboration, and measurable impact."
    )

    responsibilities = [
        f"Design, build, and maintain solutions using {', '.join(req[:3]) or 'our core stack'}.",
        "Collaborate with cross-functional partners to turn requirements into shipped features.",
        "Write clean, well-tested, maintainable code and participate in reviews.",
        "Own delivery from planning through deployment and monitoring.",
        "Continuously improve quality, performance, and developer experience.",
    ]

    requirements = [f"{exp} of relevant professional experience."]
    if req:
        requirements.append(f"Hands-on proficiency with {', '.join(req)}.")
    if job.education:
        requirements.append(f"{job.education} or equivalent practical experience.")
    requirements.append("Strong communication and problem-solving skills.")

    preferred_qualifications = ([f"Experience with {', '.join(pref)}." ] if pref else []) + [
        f"Exposure to {(job.department or 'a fast-paced product')} environments.",
    ]
    if job.certifications:
        preferred_qualifications.append(f"Certifications: {', '.join(job.certifications)}.")

    benefits = [
        "Competitive compensation" + (f" ({job.salary_currency} {job.salary_min:g}-{job.salary_max:g})"
                                      if job.salary_min and job.salary_max else ""),
        f"{mode or 'Flexible'} working arrangement",
        "Health, wellness, and learning budget",
        "Meaningful equity / growth opportunities",
    ]

    hiring_timeline = [
        {"stage": "Application review", "duration": "2-3 days"},
        {"stage": "Recruiter screen", "duration": "30 min"},
        {"stage": "Technical / skills assessment", "duration": "1 round"},
        {"stage": "Final interview", "duration": "45-60 min"},
        {"stage": "Offer", "duration": "within 1 week"},
    ]

    interview_plan = [
        {"round": "Recruiter screen", "focus": "Motivation, communication, logistics"},
        {"round": "Technical interview", "focus": f"Core skills: {', '.join(req[:4]) or title}"},
        {"round": "System / problem solving", "focus": "Design and trade-off reasoning"},
        {"round": "Team & culture fit", "focus": "Collaboration, ownership, values"},
    ]

    skill_assessment = [
        {"area": s, "type": "practical"} for s in (req[:5] or [title])
    ]

    technical_questions = [
        f"Walk me through a project where you used {req[0]}." if req else f"Describe a {title} project you're proud of.",
        "How do you approach debugging a hard, intermittent issue in production?",
        f"What trade-offs do you weigh when designing with {req[1] if len(req) > 1 else 'your stack'}?",
        "How do you ensure the quality and reliability of what you ship?",
    ]

    hr_questions = [
        "Tell me about yourself and what draws you to this role.",
        "Describe a time you disagreed with a teammate and how you resolved it.",
        "How do you prioritize when everything feels urgent?",
        "Where do you want to grow in the next two years?",
    ]

    return {
        "description": description,
        "responsibilities": responsibilities,
        "requirements": requirements,
        "preferred_qualifications": preferred_qualifications,
        "benefits": benefits,
        "hiring_timeline": hiring_timeline,
        "interview_plan": interview_plan,
        "skill_assessment": skill_assessment,
        "technical_questions": technical_questions,
        "hr_questions": hr_questions,
    }


def _ai_refine(job, base: Dict) -> Dict | None:
    prompt = f"""You are an expert technical recruiter writing a job posting.
Return ONLY a JSON object with these exact keys:
description (string), responsibilities (list of strings), requirements (list of strings),
preferred_qualifications (list of strings), benefits (list of strings),
hiring_timeline (list of objects with stage+duration),
interview_plan (list of objects with round+focus),
skill_assessment (list of objects with area+type),
technical_questions (list of strings), hr_questions (list of strings).

Job details:
- Title: {job.title}
- Company: {job.company or 'N/A'}
- Department: {job.department or 'N/A'}
- Employment: {job.employment_type or 'N/A'} / {job.work_mode or 'N/A'} / {job.location or 'N/A'}
- Experience: {_fmt_exp(job)}
- Required skills: {job.required_skills or []}
- Preferred skills: {job.preferred_skills or []}
- Education: {job.education or 'N/A'}

Write specific, professional, inclusive content. No markdown, JSON only."""
    data = extract_json(chat(prompt, temperature=0.4, max_tokens=1800))
    if not isinstance(data, dict):
        return None
    # Keep only recognized keys with non-empty values.
    return {k: data[k] for k in _GENERATED_KEYS if data.get(k)}


def generate_job_content(job) -> Dict:
    """Return a complete generated posting (AI-refined when available)."""
    base = _deterministic(job)
    ai = _ai_refine(job, base)
    if ai:
        base.update(ai)
        logger.info("Job %s content generated (AI-refined)", getattr(job, "id", "?"))
    else:
        logger.info("Job %s content generated (deterministic)", getattr(job, "id", "?"))
    return base
