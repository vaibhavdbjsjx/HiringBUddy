"""
Offline-first resume parser.

Primary path is deterministic regex + keyword extraction that ALWAYS returns a
complete, well-typed structure (so a candidate is never stuck "processing").
The AI layer (SambaNova / OpenAI compatible) runs afterwards purely to *enrich*
and refine the deterministic result when a key is available.
"""
from __future__ import annotations

import io
import json
import logging
import re
from typing import Dict, List, Optional

from pypdf import PdfReader
from services.ai_client import get_client, AI_MODEL as _AI_MODEL

logger = logging.getLogger("hiringbuddy.parser")

# Shared AI provider (SambaNova/OpenAI-compatible); None when no key configured.
client = get_client()

# ---------------------------------------------------------------------------
# Skill dictionary (canonical name -> aliases searched in text)
# ---------------------------------------------------------------------------
SKILL_ALIASES: Dict[str, List[str]] = {
    "python": ["python"], "java": [r"\bjava\b"], "c++": [r"c\+\+"], "c#": [r"c#"],
    "c": [r"\bc\b(?!\+|#)"], "javascript": ["javascript", r"\bjs\b"],
    "typescript": ["typescript", r"\bts\b"], "react": ["react", "react.js", "reactjs"],
    "node.js": ["node.js", "nodejs", "node js"], "vue.js": ["vue.js", "vuejs", "vue"],
    "angular": ["angular"], "html": ["html", "html5"], "css": ["css", "css3"],
    "tailwind": ["tailwind"], "sass": ["sass", "scss"], "redux": ["redux"],
    "next.js": ["next.js", "nextjs"], "mongodb": ["mongodb", "mongo"], "sql": [r"\bsql\b"],
    "mysql": ["mysql"], "postgresql": ["postgresql", "postgres"], "redis": ["redis"],
    "graphql": ["graphql"], "rest api": ["rest api", "restful", "rest"],
    "machine learning": ["machine learning", r"\bml\b"], "deep learning": ["deep learning"],
    "ai": [r"\bai\b", "artificial intelligence"], "nlp": ["nlp", "natural language"],
    "llm": ["llm", "large language model"], "tensorflow": ["tensorflow"], "pytorch": ["pytorch"],
    "scikit-learn": ["scikit-learn", "sklearn"], "pandas": ["pandas"], "numpy": ["numpy"],
    "opencv": ["opencv"], "aws": [r"\baws\b", "amazon web services"], "azure": ["azure"],
    "gcp": [r"\bgcp\b", "google cloud"], "docker": ["docker"], "kubernetes": ["kubernetes", "k8s"],
    "terraform": ["terraform"], "ansible": ["ansible"], "jenkins": ["jenkins"],
    "ci/cd": ["ci/cd", "cicd"], "git": [r"\bgit\b"], "linux": ["linux"], "bash": ["bash"],
    "fastapi": ["fastapi"], "flask": ["flask"], "django": ["django"], "spring boot": ["spring boot", "spring"],
    "kotlin": ["kotlin"], "swift": ["swift"], "objective-c": ["objective-c", "objective c"],
    "android": ["android"], "ios": [r"\bios\b"], "flutter": ["flutter"], "dart": ["dart"],
    "firebase": ["firebase"], "php": ["php"], "laravel": ["laravel"], "ruby": ["ruby"],
    "rails": ["rails"], "go": [r"\bgolang\b", r"\bgo\b"], "rust": ["rust"],
    "kafka": ["kafka"], "rabbitmq": ["rabbitmq"], "spark": ["spark"], "airflow": ["airflow"],
    "hadoop": ["hadoop"], "tableau": ["tableau"], "power bi": ["power bi", "powerbi"],
    "excel": ["excel"], "figma": ["figma"], "adobe xd": ["adobe xd"], "sketch": ["sketch"],
    "photoshop": ["photoshop"], "ui/ux": ["ui/ux", "ux", "user experience"],
    "wireframing": ["wireframing"], "prototyping": ["prototyping"], "wordpress": ["wordpress"],
    "webflow": ["webflow"], "cybersecurity": ["cybersecurity", "cyber security"],
    "penetration testing": ["penetration testing", "pentest"], "network security": ["network security"],
    "ethical hacking": ["ethical hacking"], "cryptography": ["cryptography"],
    "data structures": ["data structures", "dsa"], "algorithms": ["algorithms"],
    "microservices": ["microservices"], "agile": ["agile"], "scrum": ["scrum"],
    "etl": [r"\betl\b"], "statistics": ["statistics"], "r": [r"\br\b(?= programming| language)"],
}

DEGREE_PATTERNS = [
    r"\b(b\.?tech|bachelor of technology)\b", r"\b(m\.?tech|master of technology)\b",
    r"\b(b\.?e\.?|bachelor of engineering)\b", r"\b(b\.?sc|bachelor of science)\b",
    r"\b(m\.?sc|master of science)\b", r"\b(bca)\b", r"\b(mca)\b", r"\b(b\.?com)\b",
    r"\b(mba|master of business)\b", r"\b(ph\.?d|doctorate)\b", r"\b(diploma)\b",
    r"\b(bachelor'?s?)\b", r"\b(master'?s?)\b",
]

LANGUAGE_KEYWORDS = ["english", "hindi", "kannada", "tamil", "telugu", "spanish", "french",
                     "german", "japanese", "mandarin", "chinese", "marathi", "bengali",
                     "gujarati", "malayalam", "punjabi", "arabic", "portuguese", "russian"]


# ---------------------------------------------------------------------------
# PDF text extraction (3-layer fallback)
# ---------------------------------------------------------------------------
def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    text = ""
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
        if text.strip():
            logger.info("PDF: extracted %d chars via pypdf", len(text))
            return text
    except Exception as e:
        logger.warning("pypdf extraction failed: %s", e)

    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
        if text.strip():
            logger.info("PDF: extracted %d chars via pdfplumber", len(text))
            return text
    except Exception as e:
        logger.warning("pdfplumber extraction failed: %s", e)

    try:
        from pdfminer.high_level import extract_text as pm_extract
        text = pm_extract(io.BytesIO(pdf_bytes))
        if text.strip():
            logger.info("PDF: extracted %d chars via pdfminer", len(text))
            return text
    except Exception as e:
        logger.warning("pdfminer extraction failed: %s", e)

    logger.error("All PDF extraction methods failed; returning empty text")
    return text


# ---------------------------------------------------------------------------
# Deterministic field extractors
# ---------------------------------------------------------------------------
def _find_skills(text_lower: str) -> List[str]:
    found = []
    for canonical, aliases in SKILL_ALIASES.items():
        for alias in aliases:
            try:
                if re.search(alias, text_lower):
                    found.append(canonical)
                    break
            except re.error:
                if alias in text_lower:
                    found.append(canonical)
                    break
    return sorted(set(found))


def _find_name(text: str, email: Optional[str]) -> str:
    # Heuristic: first non-empty line that looks like a person's name.
    for raw in text.splitlines()[:8]:
        line = raw.strip()
        if not line or "@" in line or any(ch.isdigit() for ch in line):
            continue
        words = line.split()
        if 1 < len(words) <= 4 and all(w[:1].isalpha() for w in words) and len(line) < 45:
            if not any(k in line.lower() for k in ["resume", "curriculum", "cv", "profile"]):
                return line.title()
    # Fallback: derive from email local-part
    if email:
        local = re.split(r"[._0-9]+", email.split("@")[0])
        parts = [p for p in local if p]
        if parts:
            return " ".join(p.capitalize() for p in parts)
    return "Unknown"


def _find_education(text: str) -> List[str]:
    found = []
    lower = text.lower()
    for pat in DEGREE_PATTERNS:
        m = re.search(pat, lower)
        if m:
            found.append(m.group(0).strip().title())
    return sorted(set(found))


def _find_experience_years(text: str) -> float:
    lower = text.lower()
    years = []
    for m in re.finditer(r"(\d{1,2}(?:\.\d)?)\s*\+?\s*years?", lower):
        try:
            years.append(float(m.group(1)))
        except ValueError:
            pass
    if years:
        return min(max(years), 40.0)
    # Infer from date ranges like 2019-2023 / 2020 - present
    spans = re.findall(r"(20\d{2})\s*[-–to]+\s*(20\d{2}|present|current)", lower)
    total = 0
    for start, end in spans:
        try:
            e = 2026 if end in ("present", "current") else int(end)
            total = max(total, e - int(start))
        except ValueError:
            pass
    return float(min(total, 40))


# Any of these headers ends a captured section.
_SECTION_HEADERS = (r"experience|education|skills?|certifications?|certificates?|projects?|"
                    r"achievements?|strengths?|languages?|interests?|hobbies|declaration|"
                    r"summary|objective|awards?|publications?|references?|contact")


def _clean_line(line: str) -> str:
    """Strip leading bullets and non-printable/control characters (e.g. \\x7f)."""
    line = "".join(ch for ch in line if ch.isprintable() or ch == " ")
    return line.strip(" \t•-–*·●▪◦→»")


def _is_section_header(low: str) -> bool:
    return bool(re.match(rf"^({_SECTION_HEADERS})\s*[:]?\s*$", low)) or \
           bool(re.match(rf"^({_SECTION_HEADERS})\b", low))


def _find_projects(text: str) -> List[str]:
    projects = []
    capture = False
    for raw in text.splitlines():
        stripped = _clean_line(raw)
        low = stripped.lower()
        if re.match(r"^(projects?|personal projects?|academic projects?)\b", low):
            capture = True
            continue
        if capture:
            if _is_section_header(low) and not low.startswith("project"):
                break
            if len(stripped) > 12 and not stripped.isupper():
                projects.append(stripped[:180])
            if len(projects) >= 6:
                break
    return projects


def _find_certifications(text: str) -> List[str]:
    certs = []
    capture = False
    for raw in text.splitlines():
        stripped = _clean_line(raw)
        low = stripped.lower()
        if re.match(r"^(certifications?|certificates?|licenses?)\b", low):
            capture = True
            continue
        if capture:
            if _is_section_header(low) and not low.startswith(("cert", "licens")):
                break
            if len(stripped) > 5 and not stripped.isupper():
                certs.append(stripped[:150])
            if len(certs) >= 8:
                break
    # Also catch inline "AWS Certified ..." style mentions
    for m in re.finditer(r"([A-Z][\w ]*?(?:Certified|Certification)[\w ]*)", text):
        certs.append(_clean_line(m.group(1))[:150])
    return [c for c in dict.fromkeys(certs) if c][:8]


def _find_languages(text: str) -> List[str]:
    lower = text.lower()
    return sorted({lang.title() for lang in LANGUAGE_KEYWORDS if re.search(rf"\b{lang}\b", lower)})


def _find_links(text: str) -> Dict[str, List[str]]:
    urls = re.findall(r"(https?://[^\s)\]]+|(?:www\.)?[\w.-]+\.[a-z]{2,}/[^\s)\]]+)", text, re.I)
    github, linkedin, portfolio = [], [], []
    for u in urls:
        u = u.rstrip(".,;)")
        lu = u.lower()
        if "github.com" in lu:
            github.append(u)
        elif "linkedin.com" in lu:
            linkedin.append(u)
        elif any(bad in lu for bad in ["gmail", "outlook", "yahoo"]):
            continue
        elif "." in lu:
            portfolio.append(u)
    dedup = lambda xs: list(dict.fromkeys(xs))
    return {"github": dedup(github), "linkedin": dedup(linkedin), "portfolio": dedup(portfolio)}


def extract_offline(text: str) -> Dict:
    """Full deterministic extraction. Always returns a complete structure."""
    text = text or ""
    lower = text.lower()

    emails = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)
    phones = re.findall(r"(?:(?:\+|00)\d{1,3}[\s-]?)?(?:\(?\d{3,5}\)?[\s-]?)\d{3}[\s-]?\d{3,4}", text)
    links = _find_links(text)
    email = emails[0] if emails else None

    return {
        "name": _find_name(text, email),
        "email": email,
        "phone": phones[0].strip() if phones else None,
        "skills": _find_skills(lower),
        "education": _find_education(text),
        "experience_years": _find_experience_years(text),
        "projects": _find_projects(text),
        "certifications": _find_certifications(text),
        "languages": _find_languages(text),
        "github_links": links["github"],
        "linkedin_links": links["linkedin"],
        "portfolio_links": links["portfolio"],
        "inferred_role": None,  # filled by role_engine / AI
    }


# ---------------------------------------------------------------------------
# AI enrichment (optional)
# ---------------------------------------------------------------------------
def _ai_enrich(resume_text: str) -> Optional[Dict]:
    if not client:
        return None
    prompt = f"""You are an expert HR resume parser. Extract structured data from the resume.
Return ONLY a valid JSON object with these exact keys:
- name (string)
- email (string or null)
- phone (string or null)
- skills (list of strings, lowercase canonical tech skills)
- education (list of strings)
- experience_years (float)
- projects (list of short strings)
- certifications (list of strings)
- languages (list of spoken languages)
- github_links (list of strings)
- linkedin_links (list of strings)
- portfolio_links (list of strings)
- inferred_role (string, primary job role e.g. "Frontend Developer")

Resume Text:
{resume_text[:8000]}
"""
    try:
        resp = client.chat.completions.create(
            model=_AI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
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
        logger.warning("AI enrichment failed (using offline result): %s", e)
        return None


def _merge(base: Dict, ai: Dict) -> Dict:
    """Merge AI result into deterministic base. Union lists, prefer richer values."""
    merged = dict(base)
    list_keys = ["skills", "education", "projects", "certifications", "languages",
                 "github_links", "linkedin_links", "portfolio_links"]
    for k in list_keys:
        combined = list(base.get(k) or []) + [x for x in (ai.get(k) or []) if x]
        seen, out = set(), []
        for item in combined:
            key = str(item).strip().lower()
            if key and key not in seen:
                seen.add(key)
                out.append(item if k not in ("skills",) else str(item).strip().lower())
        merged[k] = out
    # Scalars: prefer non-empty AI value only when base is missing
    for k in ["name", "email", "phone", "inferred_role"]:
        if not base.get(k) or base.get(k) == "Unknown":
            if ai.get(k):
                merged[k] = ai[k]
    try:
        ai_exp = float(ai.get("experience_years") or 0)
        merged["experience_years"] = max(float(base.get("experience_years") or 0), ai_exp)
    except (TypeError, ValueError):
        pass
    return merged


def parse_resume_with_ai(resume_text: str) -> Dict:
    """Public entry point. Offline extraction first, AI enrichment second.

    Guaranteed to return a complete dict (never raises), so the pipeline can
    always persist a candidate and move on.
    """
    base = extract_offline(resume_text)
    ai = _ai_enrich(resume_text)
    result = _merge(base, ai) if ai else base
    result["resume_text"] = resume_text  # role_engine reads this for text signals
    logger.info(
        "Parsed resume: name=%s email=%s skills=%d exp=%.1f",
        result.get("name"), result.get("email"),
        len(result.get("skills") or []), result.get("experience_years") or 0.0,
    )
    return result
