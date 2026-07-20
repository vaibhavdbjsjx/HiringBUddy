from datetime import datetime
from pydantic import BaseModel
from typing import List, Optional, Any

class CandidateBase(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    skills: Optional[List[str]] = []
    experience_years: float = 0.0
    role_applied: Optional[str] = None
    education: Optional[List[str]] = []
    languages: Optional[List[str]] = []

class CandidateCreate(CandidateBase):
    pass

class CandidateResponse(CandidateBase):
    id: int
    truth_score: float
    truth_score_breakdown: Optional[dict] = None
    integrity_score: float
    overall_score: float
    red_flags: Optional[List[str]] = []
    hidden_talent_tag: bool
    status: str
    resume_file_path: Optional[str] = None
    
    # Advanced Intelligence Features
    multi_signal_skills: Optional[List[dict]] = []
    detailed_warnings: Optional[List[dict]] = []
    consistency_data: Optional[dict] = None
    role_match_data: Optional[dict] = None
    decision_data: Optional[dict] = None

    # Scheduling Features
    scheduled_date: Optional[str] = None
    scheduled_time: Optional[str] = None
    interview_link: Optional[str] = None
    interview_type: Optional[str] = None
    interview_token: Optional[str] = None
    interview_status: Optional[str] = None

    # Live interview + proctoring results
    interview_score: Optional[float] = 0.0
    proctoring_warnings: Optional[List[dict]] = []
    interview_report: Optional[dict] = None
    
    # Decision-Support AI Features
    projects_analysis: Optional[dict] = None
    smart_questions: Optional[dict] = None
    hr_insights: Optional[dict] = None
    candidate_category: Optional[str] = None
    email_status: Optional[str] = None
    notes: Optional[str] = None

    # Additional Contact Info
    linkedin: Optional[str] = None
    github: Optional[str] = None
    portfolio: Optional[str] = None

    # New Intelligence Features
    github_intelligence: Optional[dict] = None
    certification_intelligence: Optional[dict] = None
    interview_risk_analysis: Optional[dict] = None

    class Config:
        from_attributes = True

class SettingsResponse(BaseModel):
    smtp_email: Optional[str] = None
    smtp_password: Optional[str] = None
    sender_name: Optional[str] = None
    company_name: Optional[str] = None
    invite_template: str
    reject_template: str
    shortlist_template: str

class SettingsUpdate(BaseModel):
    smtp_email: Optional[str] = None
    smtp_password: Optional[str] = None
    sender_name: Optional[str] = None
    company_name: Optional[str] = None
    invite_template: Optional[str] = None
    reject_template: Optional[str] = None
    shortlist_template: Optional[str] = None

class ScheduleInterviewRequest(BaseModel):
    candidate_email: str
    date: str
    time: str
    mode: str

class EmailRequest(BaseModel):
    candidate_email: str

class InterviewQuestion(BaseModel):
    question: str
    difficulty: str

class InterviewFeedback(BaseModel):
    candidate_id: int
    feedback: str
    score: float


# ---------------------------------------------------------------------------
# Jobs
# ---------------------------------------------------------------------------
class JobBase(BaseModel):
    title: str
    department: Optional[str] = None
    company: Optional[str] = None
    employment_type: Optional[str] = None
    work_mode: Optional[str] = None
    location: Optional[str] = None
    experience_min: float = 0.0
    experience_max: Optional[float] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: Optional[str] = "USD"
    openings: int = 1
    notice_period: Optional[str] = None
    required_skills: Optional[List[str]] = []
    preferred_skills: Optional[List[str]] = []
    certifications: Optional[List[str]] = []
    education: Optional[str] = None


class JobCreate(JobBase):
    pass


class JobUpdate(BaseModel):
    title: Optional[str] = None
    department: Optional[str] = None
    company: Optional[str] = None
    employment_type: Optional[str] = None
    work_mode: Optional[str] = None
    location: Optional[str] = None
    experience_min: Optional[float] = None
    experience_max: Optional[float] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: Optional[str] = None
    openings: Optional[int] = None
    notice_period: Optional[str] = None
    required_skills: Optional[List[str]] = None
    preferred_skills: Optional[List[str]] = None
    certifications: Optional[List[str]] = None
    education: Optional[str] = None
    status: Optional[str] = None
    # AI-generated content (editable by the recruiter)
    description: Optional[str] = None
    responsibilities: Optional[Any] = None
    requirements: Optional[Any] = None
    preferred_qualifications: Optional[Any] = None
    benefits: Optional[Any] = None
    hiring_timeline: Optional[Any] = None
    interview_plan: Optional[Any] = None
    skill_assessment: Optional[Any] = None
    technical_questions: Optional[Any] = None
    hr_questions: Optional[Any] = None


class JobResponse(JobBase):
    id: int
    status: str
    public_slug: Optional[str] = None
    description: Optional[str] = None
    responsibilities: Optional[Any] = None
    requirements: Optional[Any] = None
    preferred_qualifications: Optional[Any] = None
    benefits: Optional[Any] = None
    hiring_timeline: Optional[Any] = None
    interview_plan: Optional[Any] = None
    skill_assessment: Optional[Any] = None
    technical_questions: Optional[Any] = None
    hr_questions: Optional[Any] = None
    application_count: Optional[int] = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------
class ApplicationCreate(BaseModel):
    candidate_id: Optional[int] = None
    source: Optional[str] = "manual"
    cover_letter: Optional[str] = None
    expected_salary: Optional[str] = None
    notice_period: Optional[str] = None
    answers: Optional[dict] = None


class ApplicationStatusUpdate(BaseModel):
    status: str


class ApplicationResponse(BaseModel):
    id: int
    job_id: int
    candidate_id: Optional[int] = None
    status: str
    source: Optional[str] = None
    match_score: Optional[float] = None
    expected_salary: Optional[str] = None
    notice_period: Optional[str] = None
    cover_letter: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = None
    organization_name: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str] = None
    role: str
    organization_id: Optional[int] = None

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ---------------------------------------------------------------------------
# Assessments (skill tests)
# ---------------------------------------------------------------------------
class AssessmentGenerateRequest(BaseModel):
    role: Optional[str] = None
    skills: Optional[List[str]] = []
    num_questions: int = 5
    candidate_id: Optional[int] = None


class AssessmentQuestion(BaseModel):
    question: str
    options: List[str]
    difficulty: Optional[str] = None
    topic: Optional[str] = None


class AssessmentResponse(BaseModel):
    id: int
    role: Optional[str] = None
    status: str
    score: Optional[float] = None
    questions: List[AssessmentQuestion]


class AssessmentSubmit(BaseModel):
    answers: List[int]
