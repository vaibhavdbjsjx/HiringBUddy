"""
Candidate evaluation engine.

Offline-first: a deterministic baseline is always computed from the parsed data
and the role-match analysis, so the dashboard shows real numbers even with no AI
key. When AI is available it *enriches* the qualitative fields (strengths,
warnings, interview questions, risk narrative).
"""
from __future__ import annotations

import json
import logging
from typing import Dict, List, Optional

from services.role_engine import analyze_role
from services.ai_client import get_client, AI_MODEL as _AI_MODEL

logger = logging.getLogger("hiringbuddy.skill_engine")

# Shared AI provider (SambaNova/OpenAI-compatible); None when no key configured.
client = get_client()


def _category(overall: float) -> str:
    if overall >= 80:
        return "Top Talent"
    if overall >= 65:
        return "Strong Candidate"
    if overall >= 45:
        return "Potential Fit"
    return "Needs Review"


def _decision(overall: float) -> Dict:
    if overall >= 75:
        decision, risk = "Recommend for Interview", "Low"
    elif overall >= 55:
        decision, risk = "Consider", "Medium"
    else:
        decision, risk = "Needs Manual Review", "High"
    return {
        "confidence_score": overall,
        "decision": decision,
        "risk_level": risk,
        "risk_reasons": [],
    }


def _deterministic_baseline(parsed: Dict, role_match: Dict) -> Dict:
    """Build a complete evaluation from the parsed data + role match, no AI."""
    overall = role_match["overall_match"]
    skills = parsed.get("skills") or []
    missing = role_match.get("missing_skills") or []

    multi_signal = [
        {"name": s, "score": 80, "evidence": ["Listed on resume"], "confidence": "medium"}
        for s in skills[:12]
    ]

    warnings: List[Dict] = []
    if not parsed.get("email"):
        warnings.append({"skill": "Contact", "reason": "No email found on resume", "severity": "medium"})
    if (parsed.get("experience_years") or 0) == 0:
        warnings.append({"skill": "Experience", "reason": "No explicit experience detected", "severity": "low"})
    if role_match["skills_match"] < 40:
        warnings.append({"skill": "Role Fit", "reason": "Few required skills for detected role", "severity": "high"})

    projects = parsed.get("projects") or []
    projects_analysis = {
        "projects": [
            {"name": (str(p)[:60] or "Project"), "tech": [], "complexity": "medium", "score": 60}
            for p in projects[:5]
        ]
    }

    strengths = [f"Matches {role_match['skills_match']}% of {role_match['role']} core skills"]
    if parsed.get("certifications"):
        strengths.append(f"{len(parsed['certifications'])} certification(s) listed")
    if parsed.get("github_links"):
        strengths.append("Has a public GitHub profile")

    return {
        "multi_signal_skills": multi_signal,
        "detailed_warnings": warnings,
        "consistency_data": {
            "consistency_score": min(100, 60 + int(role_match["experience_match"] / 5)),
            "issues": [],
        },
        "role_match_data": {
            "role_applied": role_match["role"],
            "role_match": role_match["overall_match"],
            "skills_match": role_match["skills_match"],
            "experience_match": role_match["experience_match"],
            "certification_match": role_match["certification_match"],
            "project_match": role_match["project_match"],
            "overall_match": role_match["overall_match"],
            "matched_skills": role_match["matched_skills"],
            "missing_skills": missing,
            "recommendation": role_match["recommendation"],
        },
        "projects_analysis": projects_analysis,
        "smart_questions": {"questions": _fallback_questions(role_match["role"], missing)},
        "decision_data": {**_decision(overall), "risk_reasons": [w["reason"] for w in warnings]},
        "hr_insights": {
            "summary": f"{_category(overall)} for {role_match['role']} ({overall}% overall match).",
            "recommendation": role_match["recommendation"],
            "next_action": "Schedule interview" if overall >= 65 else "Review resume manually",
            "strengths": strengths,
            "weaknesses": [f"Missing: {', '.join(missing[:5])}"] if missing else [],
        },
        "github_intelligence": {
            "evidence_score": 70 if parsed.get("github_links") else 0,
            "github_confidence": "medium" if parsed.get("github_links") else "none",
            "repository_strength": "unknown",
        },
        "certification_intelligence": {
            "certification_score": role_match["certification_match"],
            "supported_skills": parsed.get("certifications", [])[:5],
        },
        "interview_risk_analysis": {
            "risk_profile": [w["reason"] for w in warnings],
            "overall_risk_score": max(0, 100 - int(overall)),
        },
        "candidate_category": _category(overall),
        "hidden_talent_tag": overall >= 70 and (parsed.get("experience_years") or 0) < 2,
    }


def _fallback_questions(role: str, missing: List[str]) -> List[str]:
    qs = [
        f"Walk me through a {role} project you are most proud of and your specific contribution.",
        "Describe a technically challenging bug you solved and how you approached it.",
        "How do you keep your skills current in a fast-moving field?",
    ]
    for skill in missing[:2]:
        qs.append(f"Your resume doesn't mention {skill} — do you have any exposure to it?")
    return qs


def _ai_enrich(resume_text: str, parsed: Dict, baseline: Dict) -> Optional[Dict]:
    if not client:
        return None
    prompt = f"""You are an expert technical HR evaluator. A deterministic engine already
computed the role match below. Enrich the QUALITATIVE analysis only.

Detected role: {baseline['role_match_data']['role_applied']}
Overall match: {baseline['role_match_data']['overall_match']}%
Skills: {parsed.get('skills')}
Experience years: {parsed.get('experience_years')}
Projects: {parsed.get('projects')}

Resume text:
{resume_text[:6000]}

Return STRICT JSON with keys:
- strengths (list of strings)
- weaknesses (list of strings)
- detailed_warnings (list of objects: skill, reason, severity)
- smart_questions (list of 5 tailored interview question strings)
- summary (string, 2 sentences)
"""
    try:
        resp = client.chat.completions.create(
            model=_AI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        content = resp.choices[0].message.content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        return json.loads(content.strip())
    except Exception as e:
        logger.warning("AI evaluation enrichment failed (using baseline): %s", e)
        return None


def evaluate_truth_score(resume_text: str, parsed_data: dict,
                         role_match: Optional[dict] = None) -> dict:
    """Evaluate a candidate. Never raises; always returns a complete structure."""
    if role_match is None:
        role_match = analyze_role(parsed_data)

    baseline = _deterministic_baseline(parsed_data, role_match)

    ai = _ai_enrich(resume_text, parsed_data, baseline)
    if ai:
        if ai.get("smart_questions"):
            baseline["smart_questions"] = {"questions": ai["smart_questions"]}
        if ai.get("detailed_warnings"):
            baseline["detailed_warnings"] = ai["detailed_warnings"]
        if ai.get("strengths"):
            baseline["hr_insights"]["strengths"] = ai["strengths"]
        if ai.get("weaknesses"):
            baseline["hr_insights"]["weaknesses"] = ai["weaknesses"]
        if ai.get("summary"):
            baseline["hr_insights"]["summary"] = ai["summary"]

    logger.info(
        "Evaluated candidate: role=%s overall=%s category=%s ai=%s",
        role_match["role"], role_match["overall_match"],
        baseline["candidate_category"], bool(ai),
    )
    return baseline
