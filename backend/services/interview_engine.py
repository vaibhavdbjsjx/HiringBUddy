"""
AI interview engine — adaptive question generation + answer scoring.

Offline-first: a deterministic role-based question bank + heuristic scoring
always work; the AI layer refines question phrasing and answer evaluation when a
key is available. Lightweight (no ML deps) for free-tier deployment.
"""
from __future__ import annotations

import json
import logging
from typing import Dict, List, Optional

from services.ai_client import get_client, chat, AI_MODEL as _AI_MODEL

logger = logging.getLogger("hiringbuddy.interview_engine")

# Shared AI provider (SambaNova/OpenAI-compatible); None when no key configured.
client = get_client()

# Deterministic per-role question bank (difficulty progresses easy -> hard).
_ROLE_BANK: Dict[str, List[Dict]] = {
    "Frontend Developer": [
        {"question": "How does the virtual DOM improve rendering performance in React?", "difficulty": "easy", "topic": "React"},
        {"question": "Explain how you manage complex shared state across deeply nested components.", "difficulty": "medium", "topic": "State"},
        {"question": "Describe how you'd optimize a page with a poor Largest Contentful Paint score.", "difficulty": "hard", "topic": "Performance"},
    ],
    "Backend Developer": [
        {"question": "What's the difference between SQL and NoSQL, and when would you pick each?", "difficulty": "easy", "topic": "Databases"},
        {"question": "How do you design an idempotent API endpoint for payments?", "difficulty": "medium", "topic": "API Design"},
        {"question": "Walk me through how you'd scale a service handling 10k requests/second.", "difficulty": "hard", "topic": "Scalability"},
    ],
    "Data Scientist": [
        {"question": "Explain the bias-variance tradeoff with an example.", "difficulty": "easy", "topic": "ML Theory"},
        {"question": "How would you handle a highly imbalanced classification dataset?", "difficulty": "medium", "topic": "Modeling"},
        {"question": "Describe how you'd detect and prevent data leakage in a pipeline.", "difficulty": "hard", "topic": "MLOps"},
    ],
    "DevOps Engineer": [
        {"question": "What problem do containers solve compared to VMs?", "difficulty": "easy", "topic": "Containers"},
        {"question": "How do you design a zero-downtime deployment pipeline?", "difficulty": "medium", "topic": "CI/CD"},
        {"question": "Explain how you'd debug intermittent latency in a Kubernetes cluster.", "difficulty": "hard", "topic": "Observability"},
    ],
}

_GENERIC_BANK = [
    {"question": "Tell me about a project you're most proud of and your specific role in it.", "difficulty": "easy", "topic": "Experience"},
    {"question": "Describe a challenging technical bug you solved and your approach.", "difficulty": "medium", "topic": "Problem Solving"},
    {"question": "How do you keep your technical skills current?", "difficulty": "easy", "topic": "Growth"},
    {"question": "Walk me through a time you disagreed with a teammate on a technical decision.", "difficulty": "medium", "topic": "Collaboration"},
]


def generate_questions(candidate) -> List[Dict]:
    """Return an ordered, adaptive question set for a candidate.

    Prefers the role-tailored questions already produced by the resume engine,
    then tops up from the role bank / generic bank. AI refines phrasing if able.
    """
    role = getattr(candidate, "role_applied", None) or "Software Engineer"
    questions: List[Dict] = []

    # 1. Reuse role-tailored questions from resume analysis (skill_engine).
    smart = getattr(candidate, "smart_questions", None) or {}
    for i, q in enumerate((smart.get("questions") or [])[:3]):
        questions.append({"question": q, "difficulty": ["easy", "medium", "hard"][min(i, 2)],
                          "topic": "Resume-based"})

    # 2. Add role-bank questions.
    for q in _ROLE_BANK.get(role, []):
        questions.append(q)

    # 3. Top up with generic behavioural questions.
    for q in _GENERIC_BANK:
        if len(questions) >= 6:
            break
        questions.append(q)

    # Deduplicate by question text, cap at 6, order easy -> hard.
    seen, deduped = set(), []
    for q in questions:
        key = q["question"].strip().lower()
        if key not in seen:
            seen.add(key)
            deduped.append(q)
    order = {"easy": 0, "medium": 1, "hard": 2}
    deduped.sort(key=lambda q: order.get(q.get("difficulty", "medium"), 1))
    result = deduped[:6]
    logger.info("Generated %d interview questions for role=%s", len(result), role)
    return result


def _heuristic_score(answer: str) -> Dict:
    """Deterministic fallback scoring based on answer substance."""
    text = (answer or "").strip()
    words = text.split()
    n = len(words)
    if n == 0:
        return {"score": 0, "feedback": "No answer provided.",
                "communication": 0, "technical": 0, "confidence": 0}
    # Reward substance + technical vocabulary, cap fairly.
    depth = min(100, n * 2)
    tech_terms = sum(1 for w in words if len(w) > 7)
    technical = min(100, 30 + tech_terms * 4)
    communication = min(100, 40 + n)
    confidence = 60 if n > 20 else 45
    score = round(0.4 * technical + 0.35 * communication + 0.25 * confidence)
    return {"score": score, "feedback": "Answer recorded.",
            "communication": communication, "technical": technical, "confidence": confidence}


def evaluate_answer(question: str, answer: str) -> Dict:
    """Score a single answer. Never raises; AI-enhanced when available."""
    baseline = _heuristic_score(answer)
    if not client or not (answer or "").strip():
        return baseline
    try:
        resp = client.chat.completions.create(
            model=_AI_MODEL,
            messages=[{"role": "user", "content": f"""You are a technical interviewer. Score this answer 0-100 on
communication, technical knowledge, confidence, and problem solving.
Question: {question}
Answer: {answer}
Return STRICT JSON: {{"score": int, "communication": int, "technical": int,
"confidence": int, "feedback": "one sentence"}}"""}],
            temperature=0.2,
        )
        content = resp.choices[0].message.content.strip()
        for fence in ("```json", "```"):
            if content.startswith(fence):
                content = content[len(fence):]
        if content.endswith("```"):
            content = content[:-3]
        data = json.loads(content.strip())
        # Merge, keeping heuristic as backstop for missing keys.
        return {**baseline, **{k: v for k, v in data.items() if v is not None}}
    except Exception as e:
        logger.warning("AI answer evaluation failed, using heuristic: %s", e)
        return baseline


def generate_followup(question: str, answer: str) -> str:
    """Adaptive probe based on the candidate's answer. Never raises."""
    ans = (answer or "").strip()
    if len(ans.split()) < 6:
        return "Could you go deeper with a specific example from your own experience?"
    prompt = (
        "You are a technical interviewer. Given this Q&A, ask ONE short, probing "
        f"follow-up question only (no preamble).\nQ: {question}\nA: {answer}"
    )
    return chat(prompt, temperature=0.4, max_tokens=80) or "What trade-offs did you weigh in that approach?"


def interview_summary(role: str, transcript: List[Dict], report: Dict) -> str:
    """2-3 sentence hiring-manager summary. AI-written when available, else heuristic."""
    scored = [t for t in transcript if isinstance(t.get("score"), (int, float))]
    avg = report.get("interview_score", 0)
    rec = report.get("recommendation", "")
    qa = [{"q": t.get("question"), "a": (t.get("answer") or "")[:200]} for t in scored][:8]
    ai = chat(
        f"Summarize this {role} interview in 2-3 sentences for a hiring manager. "
        f"Average score {avg}/100, recommendation '{rec}'. Transcript: {qa}",
        temperature=0.3, max_tokens=180,
    )
    if ai:
        return ai
    strong = sum(1 for t in scored if (t.get("score") or 0) >= 70)
    return (
        f"Candidate completed {len(scored)} question(s) for the {role} role with an average "
        f"score of {avg}/100 ({strong} strong answer(s)). Recommendation: {rec or 'review'}."
    )


def finalize_report(role: str, transcript: List[Dict], integrity_score: float,
                    warnings: List[Dict]) -> Dict:
    """Aggregate per-answer scores + integrity into a final interview report."""
    scored = [t for t in transcript if isinstance(t.get("score"), (int, float))]
    avg = round(sum(t["score"] for t in scored) / len(scored)) if scored else 0

    def _avg(key):
        vals = [t.get(key) for t in scored if isinstance(t.get(key), (int, float))]
        return round(sum(vals) / len(vals)) if vals else 0

    dimensions = {
        "communication": _avg("communication"),
        "technical": _avg("technical"),
        "confidence": _avg("confidence"),
    }
    # Final score blends answer quality with interview integrity.
    final = round(0.8 * avg + 0.2 * integrity_score)

    if final >= 75 and integrity_score >= 80:
        recommendation = "Strong Hire"
    elif final >= 60:
        recommendation = "Hire"
    elif final >= 45:
        recommendation = "Maybe — needs another round"
    else:
        recommendation = "No Hire"

    return {
        "role": role,
        "interview_score": avg,
        "integrity_score": round(integrity_score),
        "final_score": final,
        "dimensions": dimensions,
        "questions_answered": len(scored),
        "warnings_count": len(warnings or []),
        "recommendation": recommendation,
        "summary": interview_summary(role, transcript, {"interview_score": avg, "recommendation": recommendation}),
    }
