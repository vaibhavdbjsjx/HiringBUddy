"""
Deterministic, lightweight role-detection and role-match engine.

No ML / no external API required. Pure keyword + heuristic scoring so it always
produces a result (offline-first) and is cheap enough for free-tier deployment.
The AI layer (skill_engine) can enrich these numbers but is never required.
"""
from __future__ import annotations

import logging
from typing import Dict, List, Optional

logger = logging.getLogger("hiringbuddy.role_engine")

# ---------------------------------------------------------------------------
# Role taxonomy
#   core   -> strongly indicative skills (weighted higher)
#   nice   -> supporting / bonus skills
#   min_exp-> years of experience considered a "full" match for the role
# ---------------------------------------------------------------------------
ROLE_PROFILES: Dict[str, Dict] = {
    "Frontend Developer": {
        "core": ["javascript", "typescript", "react", "html", "css", "vue.js", "angular", "redux", "tailwind"],
        "nice": ["next.js", "webpack", "vite", "figma", "sass", "ui/ux"],
        "min_exp": 1.5,
    },
    "Backend Developer": {
        "core": ["node.js", "python", "java", "go", "sql", "postgresql", "mysql", "rest api", "django", "flask", "fastapi", "spring boot"],
        "nice": ["redis", "graphql", "kafka", "rabbitmq", "microservices", "mongodb"],
        "min_exp": 2,
    },
    "Full Stack Developer": {
        "core": ["javascript", "typescript", "react", "node.js", "python", "sql", "html", "css", "rest api"],
        "nice": ["mongodb", "postgresql", "docker", "aws", "next.js", "graphql"],
        "min_exp": 2,
    },
    "Android Developer": {
        "core": ["android", "kotlin", "java", "flutter", "firebase"],
        "nice": ["jetpack compose", "room", "retrofit", "dart", "swift"],
        "min_exp": 1.5,
    },
    "iOS Developer": {
        "core": ["swift", "objective-c", "ios", "xcode"],
        "nice": ["swiftui", "combine", "cocoapods"],
        "min_exp": 1.5,
    },
    "AI Engineer": {
        "core": ["python", "machine learning", "tensorflow", "pytorch", "ai", "deep learning", "nlp", "llm"],
        "nice": ["huggingface", "langchain", "opencv", "transformers"],
        "min_exp": 2,
    },
    "ML Engineer": {
        "core": ["python", "machine learning", "tensorflow", "pytorch", "scikit-learn", "mlops"],
        "nice": ["airflow", "spark", "kubeflow", "docker", "aws"],
        "min_exp": 2,
    },
    "Data Scientist": {
        "core": ["python", "sql", "pandas", "numpy", "machine learning", "statistics", "data science"],
        "nice": ["tableau", "power bi", "r", "matplotlib", "scikit-learn"],
        "min_exp": 2,
    },
    "Data Analyst": {
        "core": ["sql", "excel", "tableau", "power bi", "python", "data analysis"],
        "nice": ["pandas", "r", "looker", "statistics"],
        "min_exp": 1,
    },
    "UI/UX Designer": {
        "core": ["figma", "ui/ux", "adobe xd", "wireframing", "prototyping", "sketch"],
        "nice": ["photoshop", "illustrator", "design systems", "html", "css"],
        "min_exp": 1.5,
    },
    "Web Designer": {
        "core": ["html", "css", "figma", "javascript", "ui/ux", "wordpress"],
        "nice": ["tailwind", "photoshop", "webflow"],
        "min_exp": 1,
    },
    "Cybersecurity Engineer": {
        "core": ["cybersecurity", "penetration testing", "network security", "linux", "ethical hacking"],
        "nice": ["burpsuite", "wireshark", "siem", "kali", "cryptography"],
        "min_exp": 2,
    },
    "Cloud Engineer": {
        "core": ["aws", "azure", "gcp", "terraform", "cloud", "linux"],
        "nice": ["kubernetes", "docker", "ansible", "cloudformation"],
        "min_exp": 2,
    },
    "DevOps Engineer": {
        "core": ["docker", "kubernetes", "jenkins", "terraform", "ansible", "ci/cd", "linux", "aws"],
        "nice": ["prometheus", "grafana", "gitlab", "helm"],
        "min_exp": 2,
    },
    "Data Engineer": {
        "core": ["python", "sql", "spark", "kafka", "airflow", "etl", "data engineering"],
        "nice": ["hadoop", "snowflake", "dbt", "aws"],
        "min_exp": 2,
    },
    "Software Engineer": {
        "core": ["python", "java", "c++", "c#", "javascript", "data structures", "algorithms", "git"],
        "nice": ["sql", "docker", "rest api", "linux"],
        "min_exp": 1.5,
    },
}

DEFAULT_ROLE = "Software Engineer"

# Certification keywords that count toward "certification match" per role family.
CERT_HINTS = ["aws", "azure", "gcp", "google", "oracle", "cisco", "comptia", "certified",
              "certification", "coursera", "udemy", "nptel", "scrum", "pmp", "tensorflow"]


def _norm(items: Optional[List[str]]) -> List[str]:
    return [str(s).strip().lower() for s in (items or []) if str(s).strip()]


def detect_role(skills: Optional[List[str]],
                text: str = "",
                inferred_role: Optional[str] = None) -> str:
    """Pick the best-fitting role from the taxonomy.

    Uses skill overlap first; falls back to raw-text keyword hits; honours a
    valid AI-inferred role as a tie-breaker bonus. Always returns a role.
    """
    skills_l = set(_norm(skills))
    text_l = (text or "").lower()
    inferred_l = (inferred_role or "").strip().lower()

    best_role, best_score = DEFAULT_ROLE, -1.0
    for role, profile in ROLE_PROFILES.items():
        core = set(profile["core"])
        nice = set(profile["nice"])

        score = 0.0
        # Skill-based signal (strongest)
        score += 3.0 * len(skills_l & core)
        score += 1.0 * len(skills_l & nice)
        # Raw-text signal (covers skills the parser missed)
        score += 1.0 * sum(1 for kw in core if kw in text_l)
        score += 0.3 * sum(1 for kw in nice if kw in text_l)
        # Honour AI-inferred role if it matches this role name
        if inferred_l and inferred_l in role.lower():
            score += 4.0

        if score > best_score:
            best_role, best_score = role, score

    if best_score <= 0 and inferred_role:
        # Nothing matched but AI gave us something usable
        return inferred_role
    return best_role


def _pct(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return 0.0
    return round(min(100.0, (numerator / denominator) * 100.0), 1)


def compute_match(role: str, parsed: Dict) -> Dict:
    """Compute per-dimension and overall match % for a candidate against a role.

    Returns a fully-populated dict even for unknown roles so downstream code and
    the UI never see missing keys.
    """
    profile = ROLE_PROFILES.get(role)
    if profile is None:
        # Unknown/custom role -> grade generically on breadth of skills.
        skills_l = _norm(parsed.get("skills"))
        breadth = _pct(len(skills_l), 8)
        exp_match = _pct(float(parsed.get("experience_years") or 0), 2)
        overall = round(0.6 * breadth + 0.4 * exp_match, 1)
        return {
            "role": role,
            "skills_match": breadth,
            "experience_match": exp_match,
            "certification_match": 100.0 if parsed.get("certifications") else 0.0,
            "project_match": min(100.0, len(parsed.get("projects") or []) * 34.0),
            "overall_match": overall,
            "matched_skills": skills_l,
            "missing_skills": [],
            "recommendation": _recommend(overall),
        }

    core = profile["core"]
    nice = profile["nice"]
    skills_l = set(_norm(parsed.get("skills")))
    text_l = (parsed.get("resume_text") or "").lower()

    def has(skill: str) -> bool:
        return skill in skills_l or skill in text_l

    matched_core = [s for s in core if has(s)]
    matched_nice = [s for s in nice if has(s)]
    missing = [s for s in core if not has(s)]

    # Skills: core carries most weight, nice gives up to a 20% bonus.
    core_pct = _pct(len(matched_core), len(core))
    nice_bonus = min(20.0, len(matched_nice) * 5.0)
    skills_match = round(min(100.0, core_pct + nice_bonus), 1)

    experience_match = _pct(float(parsed.get("experience_years") or 0), profile["min_exp"])

    certs = _norm(parsed.get("certifications"))
    relevant_certs = [c for c in certs if any(h in c for h in CERT_HINTS)]
    if not certs:
        certification_match = 0.0
    else:
        certification_match = round(min(100.0, 40.0 + len(relevant_certs) * 30.0 + len(certs) * 10.0), 1)

    projects = parsed.get("projects") or []
    # Reward both quantity and role-relevance of projects.
    proj_text = " ".join(str(p).lower() for p in projects)
    relevant_hits = sum(1 for s in core if s in proj_text)
    project_match = round(min(100.0, len(projects) * 25.0 + relevant_hits * 10.0), 1)

    overall = round(
        0.45 * skills_match
        + 0.25 * experience_match
        + 0.20 * project_match
        + 0.10 * certification_match,
        1,
    )

    return {
        "role": role,
        "skills_match": skills_match,
        "experience_match": experience_match,
        "certification_match": certification_match,
        "project_match": project_match,
        "overall_match": overall,
        "matched_skills": matched_core + matched_nice,
        "missing_skills": missing,
        "recommendation": _recommend(overall),
    }


def _recommend(overall: float) -> str:
    if overall >= 80:
        return "Strong Match - Fast-track to interview"
    if overall >= 65:
        return "Good Match - Recommend interview"
    if overall >= 45:
        return "Partial Match - Review manually"
    return "Weak Match - Likely not a fit"


def analyze_role(parsed: Dict) -> Dict:
    """Convenience entry point: detect the role then compute the match."""
    role = detect_role(
        parsed.get("skills"),
        parsed.get("resume_text", "") or "",
        parsed.get("inferred_role"),
    )
    result = compute_match(role, parsed)
    logger.info("Role analysis: role=%s overall=%s%%", role, result["overall_match"])
    return result
