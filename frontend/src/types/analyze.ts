export interface AnalyzeRequest {
  resume_text: string;
  job_description: string;
}

export interface AnalyzeResponse {
  score: number;
  strengths: string[];
  weaknesses: string[];
  missing_keywords: string[];
  rewrite_suggestions: string[];
  interview_questions: string[];
  summary: string;
}

export interface ApiError {
  error?: {
    code?: number;
    message?: string;
    details?: unknown;
  };
}
