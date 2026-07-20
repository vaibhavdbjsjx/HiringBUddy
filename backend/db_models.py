from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Float, Boolean, Text, ForeignKey, JSON, DateTime
from sqlalchemy.orm import relationship
from database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)

class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, index=True, nullable=True)  # tenant scope (D2)
    name = Column(String, index=True)
    email = Column(String, index=True, nullable=True)  # not unique: resumes may share/omit email
    phone = Column(String, nullable=True)
    resume_text = Column(Text, nullable=True)
    skills = Column(JSON, nullable=True)  # List of extracted skills
    experience_years = Column(Float, default=0.0)

    # Rich extracted profile
    role_applied = Column(String, nullable=True)   # detected target role
    education = Column(JSON, nullable=True)         # list of degrees
    languages = Column(JSON, nullable=True)         # spoken languages
    email_status = Column(String, default="none")  # none, sent, failed
    notes = Column(Text, nullable=True)            # HR free-form notes
    
    # Intelligence Engine Outputs
    truth_score = Column(Float, default=0.0)
    truth_score_breakdown = Column(JSON, nullable=True) # {"skill_match": X, "project_depth": Y, "consistency": Z}
    integrity_score = Column(Float, default=0.0) # From proctoring
    overall_score = Column(Float, default=0.0)
    red_flags = Column(JSON, nullable=True)
    hidden_talent_tag = Column(Boolean, default=False)
    
    # Advanced Intelligence Features
    multi_signal_skills = Column(JSON, nullable=True)
    detailed_warnings = Column(JSON, nullable=True)
    consistency_data = Column(JSON, nullable=True)
    role_match_data = Column(JSON, nullable=True)
    decision_data = Column(JSON, nullable=True)
    
    # Decision-Support AI Features
    projects_analysis = Column(JSON, nullable=True)
    smart_questions = Column(JSON, nullable=True)
    hr_insights = Column(JSON, nullable=True)
    candidate_category = Column(String, nullable=True)
    
    # Additional Contact Info
    linkedin = Column(String, nullable=True)
    github = Column(String, nullable=True)
    portfolio = Column(String, nullable=True)
    
    # New Intelligence Features
    github_intelligence = Column(JSON, nullable=True)
    certification_intelligence = Column(JSON, nullable=True)
    interview_risk_analysis = Column(JSON, nullable=True)
    
    resume_file_path = Column(String, nullable=True)
    
    status = Column(String, default="pending") # pending, invited, rejected, interviewed, shortlisted
    
    # Scheduling fields
    scheduled_date = Column(String, nullable=True)
    scheduled_time = Column(String, nullable=True)
    interview_link = Column(String, nullable=True)
    interview_type = Column(String, nullable=True) # "ai" or "hr"
    interview_token = Column(String, nullable=True)
    interview_token_expiry = Column(String, nullable=True)  # ISO timestamp
    interview_status = Column(String, default="not_started") # not_started, in_progress, completed

    # Live interview + proctoring results
    interview_score = Column(Float, default=0.0)       # AI interview performance 0-100
    proctoring_warnings = Column(JSON, nullable=True)  # list of {time, type, message, severity}
    interview_report = Column(JSON, nullable=True)     # final structured report

class SystemSettings(Base):
    __tablename__ = "settings"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # SMTP Configuration
    smtp_email = Column(String, nullable=True)
    smtp_password = Column(String, nullable=True)
    sender_name = Column(String, default="HiringBuddy AI")
    company_name = Column(String, default="Acme Corp")
    
    invite_template = Column(Text, default="""Dear {{candidate_name}},

Congratulations! We are pleased to invite you to an interview for the {{job_role}} position at {{company_name}}.

Date: {{interview_date}}
Time: {{interview_time}}
Meeting Link: {{interview_link}}

Please ensure you have a stable internet connection and a working webcam/microphone for the session.

Best regards,
{{hr_name}}
{{company_name}}""")

    reject_template = Column(Text, default="""Dear {{candidate_name}},

Thank you for taking the time to apply and share your background with us for the {{job_role}} position at {{company_name}}.

After careful consideration, we have decided to move forward with other candidates whose profiles more closely match the specific requirements of the role at this time.

We appreciate your interest in our company and wish you the best of luck in your job search.

Best regards,
{{hr_name}}
{{company_name}}""")

    shortlist_template = Column(Text, default="""Dear {{candidate_name}},

We are thrilled to inform you that you have been shortlisted for the {{job_role}} position at {{company_name}}! 

Our team was very impressed with your background and the skills you demonstrated. We will be reaching out soon with the next steps in our hiring process.

Best regards,
{{hr_name}}
{{company_name}}""")

class Interview(Base):
    __tablename__ = "interviews"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"))
    questions = Column(JSON, nullable=True)      # generated questions
    feedback = Column(Text, nullable=True)
    score = Column(Float, default=0.0)           # overall interview score 0-100
    integrity_score = Column(Float, default=100.0)
    warnings = Column(JSON, nullable=True)       # proctoring warnings captured
    transcript = Column(JSON, nullable=True)     # Q&A transcript
    created_at = Column(String, nullable=True)   # ISO timestamp

    candidate = relationship("Candidate")


class Job(Base):
    """A role/opening a recruiter is hiring for."""
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, index=True, nullable=True)  # tenant scope (wired in D2)

    # Core details
    title = Column(String, nullable=False, index=True)
    department = Column(String, nullable=True)
    company = Column(String, nullable=True)
    employment_type = Column(String, nullable=True)  # full_time, part_time, contract, internship, temporary
    work_mode = Column(String, nullable=True)         # remote, hybrid, onsite
    location = Column(String, nullable=True)

    experience_min = Column(Float, default=0.0)
    experience_max = Column(Float, nullable=True)
    salary_min = Column(Float, nullable=True)
    salary_max = Column(Float, nullable=True)
    salary_currency = Column(String, default="USD")
    openings = Column(Integer, default=1)
    notice_period = Column(String, nullable=True)

    required_skills = Column(JSON, nullable=True)     # list[str]
    preferred_skills = Column(JSON, nullable=True)    # list[str]
    certifications = Column(JSON, nullable=True)      # list[str]
    education = Column(String, nullable=True)

    # AI-generated content (populated by the Job Creation engine, task B1)
    description = Column(Text, nullable=True)
    responsibilities = Column(JSON, nullable=True)
    requirements = Column(JSON, nullable=True)
    preferred_qualifications = Column(JSON, nullable=True)
    benefits = Column(JSON, nullable=True)
    hiring_timeline = Column(JSON, nullable=True)
    interview_plan = Column(JSON, nullable=True)
    skill_assessment = Column(JSON, nullable=True)
    technical_questions = Column(JSON, nullable=True)
    hr_questions = Column(JSON, nullable=True)

    status = Column(String, default="draft", index=True)  # draft, open, on_hold, closed
    public_slug = Column(String, unique=True, index=True, nullable=True)

    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    applications = relationship(
        "Application", back_populates="job", cascade="all, delete-orphan"
    )


class Application(Base):
    """Links a candidate to a job with its own pipeline status."""
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), index=True, nullable=False)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), index=True, nullable=True)

    status = Column(String, default="applied", index=True)
    # applied, screening, shortlisted, interview, offer, hired, rejected
    source = Column(String, default="careers")  # careers, linkedin, indeed, referral, manual, upload
    cover_letter = Column(Text, nullable=True)
    expected_salary = Column(String, nullable=True)
    notice_period = Column(String, nullable=True)
    answers = Column(JSON, nullable=True)        # screening-question answers
    match_score = Column(Float, nullable=True)   # cached job-fit score 0-100
    stage_history = Column(JSON, nullable=True)  # list[{stage, at}]

    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    job = relationship("Job", back_populates="applications")
    candidate = relationship("Candidate")


class Organization(Base):
    """A tenant workspace. All jobs/candidates/users belong to one organization."""
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, index=True, nullable=True)
    created_at = Column(DateTime, default=_utcnow)

    users = relationship("User", back_populates="organization", cascade="all, delete-orphan")


class User(Base):
    """A recruiter/admin account within an organization."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), index=True, nullable=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    role = Column(String, default="owner")  # owner, admin, recruiter, member
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)

    organization = relationship("Organization", back_populates="users")


class Assessment(Base):
    """A generated skill test (MCQ). Correct answers live server-side only."""
    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, index=True, nullable=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), index=True, nullable=True)
    role = Column(String, nullable=True)
    skills = Column(JSON, nullable=True)
    questions = Column(JSON, nullable=True)   # includes answer_index (never sent to candidates)
    answers = Column(JSON, nullable=True)     # candidate's submitted answers
    score = Column(Float, nullable=True)
    status = Column(String, default="generated")  # generated, submitted
    created_at = Column(DateTime, default=_utcnow)
