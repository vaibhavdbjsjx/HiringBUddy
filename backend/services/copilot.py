"""Natural-language HR copilot over candidate data.

Deterministic intent handlers cover the common recruiter questions (count, top/
best, find by skill, compare, average, below-threshold) so it works offline and
predictably. Anything else falls back to the LLM with candidate data as context.
Read-only: it never mutates data (bulk actions are *suggested*, not executed).
Never raises.
"""
from __future__ import annotations

import re
from typing import Dict, List, Optional

from services.ai_client import chat


def _rank(cands: List[Dict]) -> List[Dict]:
    return sorted(cands, key=lambda c: c.get("overall_score") or 0, reverse=True)


def _slim(c: Dict) -> Dict:
    return {"id": c.get("id"), "name": c.get("name"),
            "overall_score": c.get("overall_score"), "role_applied": c.get("role_applied")}


def _find_by_name(cands: List[Dict], q: str) -> Optional[Dict]:
    q = q.strip().lower()
    return next((c for c in cands if q and q in (c.get("name") or "").lower()), None)


def _detect_skill(m: str, cands: List[Dict]) -> Optional[str]:
    skills = {s.lower() for c in cands for s in (c.get("skills") or [])}
    for s in sorted(skills, key=len, reverse=True):
        if re.search(r"\b" + re.escape(s) + r"\b", m):
            return s
    return None


def answer_query(message: str, candidates: List[Dict]) -> Dict:
    m = (message or "").lower().strip()
    total = len(candidates)
    if total == 0:
        return {"answer": "You don't have any candidates yet. Upload resumes to get started.", "candidates": []}

    if re.search(r"\bhow many\b|\bcount\b|\btotal\b", m):
        return {"answer": f"You have {total} candidate(s) in your pipeline.", "candidates": []}

    if "average" in m or "avg" in m:
        avg = round(sum((c.get("overall_score") or 0) for c in candidates) / total, 1)
        return {"answer": f"The average overall match score is {avg}%.", "candidates": []}

    cmp = re.search(r"compare (.+?) (?:and|vs|versus|with) (.+)", m)
    if cmp:
        a, b = _find_by_name(candidates, cmp.group(1)), _find_by_name(candidates, cmp.group(2))
        if a and b:
            stronger = a if (a.get("overall_score") or 0) >= (b.get("overall_score") or 0) else b
            return {
                "answer": (f"{a['name']} scores {a.get('overall_score')}% ({a.get('role_applied')}) vs "
                           f"{b['name']} at {b.get('overall_score')}% ({b.get('role_applied')}). "
                           f"Stronger match: {stronger['name']}."),
                "candidates": [_slim(a), _slim(b)],
            }

    skill = _detect_skill(m, candidates)
    if skill and re.search(r"\bfind\b|\bwho\b|\bshow\b|\bwhich\b|\blist\b", m):
        matches = _rank([c for c in candidates if skill in [s.lower() for s in (c.get("skills") or [])]])
        names = ", ".join(c["name"] for c in matches[:10]) or "none"
        return {"answer": f"{len(matches)} candidate(s) with {skill}: {names}.",
                "candidates": [_slim(c) for c in matches[:10]]}

    thr = re.search(r"(?:below|under|less than)\s*(\d+)", m)
    if thr and ("reject" in m or "below" in m or "under" in m or "less than" in m):
        cutoff = int(thr.group(1))
        low = _rank([c for c in candidates if (c.get("overall_score") or 0) < cutoff])
        names = ", ".join(c["name"] for c in low[:10]) or "none"
        return {"answer": (f"{len(low)} candidate(s) are below {cutoff}%: {names}. "
                           f"Open the dashboard to review and take bulk action."),
                "candidates": [_slim(c) for c in low[:10]]}

    tm = re.search(r"top (\d+)", m)
    if tm or re.search(r"\bbest\b|\bstrongest\b|\btop\b|\brank\b", m):
        n = int(tm.group(1)) if tm else 5
        ranked = _rank(candidates)[:n]
        lines = "; ".join(f"{c['name']} ({c.get('overall_score')}%)" for c in ranked)
        return {"answer": f"Top {len(ranked)} by match score: {lines}.",
                "candidates": [_slim(c) for c in ranked]}

    # Open-ended → LLM with candidate context.
    ctx = [{"name": c["name"], "role": c.get("role_applied"), "score": c.get("overall_score"),
            "skills": (c.get("skills") or [])[:8]} for c in _rank(candidates)[:20]]
    ai = chat(
        f"You are an HR copilot. Answer the recruiter's question using ONLY this candidate data: {ctx}. "
        f"Be concise. Question: {message}",
        temperature=0.3, max_tokens=250,
    )
    if ai:
        return {"answer": ai, "candidates": []}

    ranked = _rank(candidates)[:3]
    lines = ", ".join(f"{c['name']} ({c.get('overall_score')}%)" for c in ranked)
    return {"answer": (f"I can find, rank, and compare candidates for you. "
                       f"Your current top matches are: {lines}."),
            "candidates": [_slim(c) for c in ranked]}
