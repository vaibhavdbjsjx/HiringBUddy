"""Role-based skill assessment generation (MCQ).

AI generates tailored multiple-choice questions for a role + skill set; a
deterministic bank guarantees a valid test offline. Each question carries an
``answer_index`` that is kept server-side and never sent to candidates.
Never raises.
"""
from __future__ import annotations

import logging
from typing import Dict, List, Optional

from services.ai_client import chat, extract_json

logger = logging.getLogger("hiringbuddy.assessment")

# Small real-question bank per skill (offline fallback).
_BANK: Dict[str, List[Dict]] = {
    "python": [
        {"question": "What is the output of len(set([1, 1, 2, 3]))?",
         "options": ["4", "3", "2", "Error"], "answer_index": 1, "difficulty": "easy", "topic": "Python"},
        {"question": "Which keyword turns a function into a generator?",
         "options": ["yield", "return", "gen", "async"], "answer_index": 0, "difficulty": "medium", "topic": "Python"},
    ],
    "sql": [
        {"question": "Which clause filters aggregated groups?",
         "options": ["WHERE", "HAVING", "GROUP BY", "ORDER BY"], "answer_index": 1, "difficulty": "medium", "topic": "SQL"},
        {"question": "Which JOIN keeps all rows from the left table?",
         "options": ["INNER JOIN", "LEFT JOIN", "CROSS JOIN", "RIGHT JOIN"], "answer_index": 1, "difficulty": "easy", "topic": "SQL"},
    ],
    "javascript": [
        {"question": "What does typeof null return?",
         "options": ["'null'", "'object'", "'undefined'", "throws"], "answer_index": 1, "difficulty": "easy", "topic": "JavaScript"},
    ],
    "react": [
        {"question": "Which hook is for side effects?",
         "options": ["useState", "useEffect", "useMemo", "useRef"], "answer_index": 1, "difficulty": "easy", "topic": "React"},
    ],
    "docker": [
        {"question": "Which file defines a Docker image build?",
         "options": ["docker-compose.yml", "Dockerfile", "image.cfg", "build.sh"], "answer_index": 1, "difficulty": "easy", "topic": "Docker"},
    ],
}

_GENERIC: List[Dict] = [
    {"question": "Average-case time complexity of binary search?",
     "options": ["O(n)", "O(log n)", "O(n log n)", "O(1)"], "answer_index": 1, "difficulty": "easy", "topic": "CS"},
    {"question": "Which is NOT a standard HTTP method?",
     "options": ["GET", "POST", "FETCH", "DELETE"], "answer_index": 2, "difficulty": "easy", "topic": "Web"},
    {"question": "Average lookup time in a hash table?",
     "options": ["O(n)", "O(log n)", "O(1)", "O(n^2)"], "answer_index": 2, "difficulty": "medium", "topic": "CS"},
    {"question": "Which data structure is FIFO?",
     "options": ["Stack", "Queue", "Tree", "Heap"], "answer_index": 1, "difficulty": "easy", "topic": "CS"},
    {"question": "What does 'idempotent' mean for an API call?",
     "options": ["Always fails", "Same result on repeat", "Requires auth", "Runs async"], "answer_index": 1, "difficulty": "medium", "topic": "API"},
]

_ORDER = {"easy": 0, "medium": 1, "hard": 2}


def _valid(q: dict) -> bool:
    return (
        isinstance(q, dict)
        and isinstance(q.get("question"), str)
        and isinstance(q.get("options"), list)
        and len(q["options"]) >= 2
        and isinstance(q.get("answer_index"), int)
        and 0 <= q["answer_index"] < len(q["options"])
    )


def _fallback(skills: List[str], num: int) -> List[Dict]:
    out: List[Dict] = []
    seen = set()
    for s in skills:
        for q in _BANK.get(s.lower(), []):
            if q["question"] not in seen:
                out.append(dict(q))
                seen.add(q["question"])
    for q in _GENERIC:
        if len(out) >= num:
            break
        if q["question"] not in seen:
            out.append(dict(q))
            seen.add(q["question"])
    out.sort(key=lambda q: _ORDER.get(q.get("difficulty", "easy"), 0))
    return out[:num]


def _ai_generate(role: str, skills: List[str], num: int) -> Optional[List[Dict]]:
    prompt = f"""Generate {num} multiple-choice technical assessment questions for a {role or 'software'} role.
Focus on these skills: {', '.join(skills) or 'general software engineering'}.
Return ONLY a JSON array; each item:
{{"question": str, "options": [4 strings], "answer_index": int (0-based correct option),
  "difficulty": "easy"|"medium"|"hard", "topic": str}}
Mix difficulties. Ensure exactly one correct option per question."""
    data = extract_json(chat(prompt, temperature=0.5, max_tokens=1500))
    if isinstance(data, dict):
        data = data.get("questions") or next((v for v in data.values() if isinstance(v, list)), None)
    if not isinstance(data, list):
        return None
    good = [q for q in data if _valid(q)]
    return good or None


def generate_assessment(role: Optional[str], skills: Optional[List[str]], num_questions: int = 5) -> List[Dict]:
    """Return a list of MCQ dicts (with server-side answer_index)."""
    skills = [s for s in (skills or []) if s]
    num = max(1, min(num_questions or 5, 15))
    questions = _ai_generate(role or "", skills, num) or _fallback(skills, num)
    if not questions:  # ultimate safety net
        questions = _GENERIC[:num]
    logger.info("Assessment generated: role=%s skills=%d -> %d questions", role, len(skills), len(questions))
    return questions[:num]
