import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

const TOKEN_KEY = 'hiringbuddy_auth_token';

// Attach the JWT to every request when the recruiter is signed in.
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY);
  if (token) {
    config.headers = config.headers ?? {};
    (config.headers as any).Authorization = `Bearer ${token}`;
  }
  return config;
});

// On 401, clear the session and return to /auth — but never from a public
// candidate page (interview / mobile camera), which has no login.
apiClient.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error?.response?.status === 401) {
      localStorage.removeItem(TOKEN_KEY);
      const p = window.location.pathname;
      const onPublicPage =
        p.startsWith('/auth') || p.includes('/c-interview') || p.includes('/mobile-cam');
      if (!onPublicPage) window.location.href = '/auth';
    }
    return Promise.reject(error);
  },
);

export interface Candidate {
  id: number;
  name: string;
  email: string;
  phone: string | null;
  skills: string[];
  experience_years: number;
  role_applied?: string | null;
  education?: string[];
  languages?: string[];
  email_status?: string | null;
  notes?: string | null;
  truth_score: number;
  truth_score_breakdown?: {
    skill_match: number;
    project_depth: number;
    consistency: number;
  };
  integrity_score: number;
  overall_score: number;
  red_flags: string[];
  hidden_talent_tag: boolean;
  status: string;
  
  // Advanced Intelligence Features
  multi_signal_skills?: {
    name: string;
    score: number;
    evidence: string[];
    confidence: string;
  }[];
  detailed_warnings?: {
    skill: string;
    reason: string;
  }[];
  consistency_data?: {
    consistency_score: number;
    issues: string[];
  };
  role_match_data?: {
    role_applied?: string;
    role_match: number;
    skills_match?: number;
    experience_match?: number;
    certification_match?: number;
    project_match?: number;
    overall_match?: number;
    matched_skills: string[];
    missing_skills: string[];
    recommendation?: string;
  };
  decision_data?: {
    confidence_score: number;
    decision: string;
    risk_level: string;
    summary: string;
  };
  
  // Scheduling
  scheduled_date?: string;
  scheduled_time?: string;
  interview_link?: string;
  interview_token?: string;
  interview_type?: string;
  
  // Decision-Support AI Features
  projects_analysis?: {
    projects: {
      name: string;
      tech: string[];
      complexity: string;
      score: number;
    }[];
  };
  smart_questions?: {
    questions: string[];
  };
  hr_insights?: {
    summary: string;
    recommendation: string;
    next_action: string;
  };
  candidate_category?: string;
  
  // New Contact Fields
  linkedin?: string | null;
  github?: string | null;
  portfolio?: string | null;

  // New Intelligence Features
  github_intelligence?: {
    evidence_score?: number;
    github_confidence?: string;
    repository_strength?: string;
  };
  certification_intelligence?: {
    certification_score?: number;
    supported_skills?: string[];
  };
  interview_risk_analysis?: {
    risk_profile?: string[];
    overall_risk_score?: number;
  };
}

export interface Analytics {
  total_candidates: number;
  avg_score: number;
  shortlisted_count: number;
  rejected_count: number;
  top_skills: { skill: string; count: number }[];
}

export const getCandidates = async (params: any = {}): Promise<Candidate[]> => {
  const response = await apiClient.get('/candidates/', { params });
  return response.data;
};

export const getCandidate = async (id: number): Promise<Candidate> => {
  const response = await apiClient.get(`/candidates/${id}`);
  return response.data;
};

export const getAnalytics = async (): Promise<Analytics> => {
  const response = await apiClient.get('/candidates/analytics');
  return response.data;
};

export const getUploadStatus = async (): Promise<{ processing: number, completed: number, total: number }> => {
  const response = await apiClient.get('/candidates/upload-status');
  return response.data;
};

export const uploadResumes = async (files: FileList): Promise<Candidate[]> => {
  const formData = new FormData();
  for (let i = 0; i < files.length; i++) {
    formData.append('files', files[i]);
  }
  
  const response = await apiClient.post('/candidates/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const rejectCandidate = async (id: number): Promise<void> => {
  await apiClient.post(`/candidates/${id}/reject`);
};

export const inviteCandidate = async (id: number): Promise<void> => {
  await apiClient.post(`/candidates/${id}/invite`);
};

export const sendEmailAction = async (action: 'invite' | 'reject' | 'shortlist', email: string): Promise<{ link?: string; email_status?: string }> => {
  const response = await apiClient.post(`/candidates/send-${action}`, { candidate_email: email });
  return response.data;
};

export const startAIInterview = async (email: string): Promise<{ status: string, interview_id: number, link: string }> => {
  const response = await apiClient.post(`/candidates/start-ai-interview`, { candidate_email: email });
  return response.data;
};

export const getResumeUrl = (candidateId: number) => {
  return `${API_URL}/candidates/resume/${candidateId}`;
};

// ---------------------------------------------------------------------------
// Interview API
// ---------------------------------------------------------------------------
export interface InterviewQuestion {
  question: string;
  difficulty: string;
  topic?: string;
}

export const verifyInterviewToken = async (id: number, token: string) => {
  const res = await apiClient.get(`/interviews/${id}/verify`, { params: { token } });
  return res.data as { valid: boolean; candidate_name: string; role: string };
};

export const getInterviewQuestions = async (id: number): Promise<{ questions: InterviewQuestion[]; role: string }> => {
  const res = await apiClient.get(`/interviews/${id}/questions`);
  return res.data;
};

export const startInterview = async (id: number) => {
  const res = await apiClient.post(`/interviews/${id}/start`);
  return res.data as { status: string; interview_id: number };
};

export const submitAnswer = async (id: number, question: string, answer: string) => {
  const res = await apiClient.post(`/interviews/${id}/answer`, { question, answer });
  return res.data as { score: number; communication: number; technical: number; confidence: number; feedback: string };
};

export const recordProctoring = async (id: number, type: string, message: string, severity: 'low' | 'medium' | 'high' = 'medium') => {
  const res = await apiClient.post(`/interviews/${id}/proctoring`, { type, message, severity });
  return res.data as { integrity_score: number; warnings_count: number };
};

export const finalizeInterview = async (id: number, transcript: any[] = [], integrity_score = 100) => {
  const res = await apiClient.post(`/interviews/${id}/finalize`, { transcript, integrity_score });
  return res.data;
};

export const getInterviewReport = async (id: number) => {
  const res = await apiClient.get(`/interviews/${id}/report`);
  return res.data;
};

export interface Settings {
  smtp_email?: string;
  smtp_password?: string;
  sender_name?: string;
  company_name?: string;
  invite_template: string;
  reject_template: string;
  shortlist_template: string;
}

export const getSettings = async (): Promise<Settings> => {
  const response = await apiClient.get('/settings/');
  return response.data;
};

export const updateSettings = async (data: Partial<Settings>): Promise<Settings> => {
  const response = await apiClient.put('/settings/', data);
  return response.data;
};

// ---------------------------------------------------------------------------
// Auth
// ---------------------------------------------------------------------------
export interface AuthUser {
  id: number;
  email: string;
  full_name?: string | null;
  role: string;
  organization_id?: number | null;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: AuthUser;
}

export const register = async (
  email: string,
  password: string,
  full_name?: string,
  organization_name?: string,
): Promise<AuthResponse> => {
  const res = await apiClient.post('/auth/register', {
    email,
    password,
    full_name,
    organization_name,
  });
  return res.data;
};

export const login = async (email: string, password: string): Promise<AuthResponse> => {
  const res = await apiClient.post('/auth/login', { email, password });
  return res.data;
};

export const getMe = async (): Promise<AuthUser> => {
  const res = await apiClient.get('/auth/me');
  return res.data;
};

export const logout = () => {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem('hiringbuddy_user');
};

// ---------------------------------------------------------------------------
// Jobs
// ---------------------------------------------------------------------------
export interface Job {
  id: number;
  title: string;
  department?: string | null;
  company?: string | null;
  employment_type?: string | null;
  work_mode?: string | null;
  location?: string | null;
  experience_min?: number;
  experience_max?: number | null;
  salary_min?: number | null;
  salary_max?: number | null;
  salary_currency?: string | null;
  openings?: number;
  required_skills?: string[];
  preferred_skills?: string[];
  education?: string | null;
  status: string;
  public_slug?: string | null;
  application_count?: number;
  description?: string | null;
  responsibilities?: string[] | null;
  requirements?: string[] | null;
  preferred_qualifications?: string[] | null;
  benefits?: string[] | null;
  hiring_timeline?: any;
  interview_plan?: any;
  skill_assessment?: any;
  technical_questions?: string[] | null;
  hr_questions?: string[] | null;
}

export interface JobCreatePayload {
  title: string;
  department?: string;
  company?: string;
  employment_type?: string;
  work_mode?: string;
  location?: string;
  experience_min?: number;
  experience_max?: number;
  salary_min?: number;
  salary_max?: number;
  required_skills?: string[];
  preferred_skills?: string[];
  education?: string;
}

export const getJobs = async (): Promise<Job[]> => (await apiClient.get('/jobs/')).data;
export const getJob = async (id: number): Promise<Job> => (await apiClient.get(`/jobs/${id}`)).data;
export const createJob = async (data: JobCreatePayload): Promise<Job> =>
  (await apiClient.post('/jobs/', data)).data;
export const updateJob = async (id: number, data: Partial<Job>): Promise<Job> =>
  (await apiClient.patch(`/jobs/${id}`, data)).data;
export const deleteJob = async (id: number): Promise<void> => {
  await apiClient.delete(`/jobs/${id}`);
};
export const generateJobContent = async (id: number): Promise<Job> =>
  (await apiClient.post(`/jobs/${id}/generate`)).data;

// ---------------------------------------------------------------------------
// HR Copilot
// ---------------------------------------------------------------------------
export interface CopilotResult {
  answer: string;
  candidates: { id: number; name: string; overall_score?: number | null; role_applied?: string | null }[];
}
export const copilotQuery = async (message: string): Promise<CopilotResult> =>
  (await apiClient.post('/copilot/query', { message })).data;

// ---------------------------------------------------------------------------
// Skill assessments
// ---------------------------------------------------------------------------
export interface AssessmentQuestion {
  question: string;
  options: string[];
  difficulty?: string | null;
  topic?: string | null;
}
export interface Assessment {
  id: number;
  role?: string | null;
  status: string;
  score?: number | null;
  questions: AssessmentQuestion[];
}
export interface AssessmentResult {
  assessment_id: number;
  score: number;
  correct: number;
  total: number;
  results: { correct_index: number; chosen: number | null; is_correct: boolean }[];
}
export const generateAssessment = async (payload: { role?: string; skills?: string[]; num_questions?: number }): Promise<Assessment> =>
  (await apiClient.post('/assessments/generate', payload)).data;
export const submitAssessment = async (id: number, answers: number[]): Promise<AssessmentResult> =>
  (await apiClient.post(`/assessments/${id}/submit`, { answers })).data;

// ---------------------------------------------------------------------------
// Public careers (no auth)
// ---------------------------------------------------------------------------
export const getPublicJob = async (slug: string): Promise<Job> =>
  (await apiClient.get(`/jobs/public/${slug}`)).data;
export const applyToJob = async (slug: string, form: FormData) =>
  (await apiClient.post(`/jobs/public/${slug}/apply`, form, { headers: { 'Content-Type': 'multipart/form-data' } })).data;
