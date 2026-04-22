from typing import List

from pydantic import BaseModel, Field, model_validator


class AnalyzeRequest(BaseModel):
    resume_text: str = Field(..., min_length=30, max_length=20000)
    job_description: str = Field(..., min_length=30, max_length=20000)

    @model_validator(mode="after")
    def check_non_empty_text(self) -> "AnalyzeRequest":
        if not self.resume_text.strip():
            raise ValueError("resume_text cannot be empty")
        if not self.job_description.strip():
            raise ValueError("job_description cannot be empty")
        return self


class AnalyzeResponse(BaseModel):
    score: int = Field(..., ge=0, le=100)
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    missing_keywords: List[str] = Field(default_factory=list)
    rewrite_suggestions: List[str] = Field(default_factory=list)
    interview_questions: List[str] = Field(default_factory=list)
    summary: str = Field(..., min_length=1)


class HealthResponse(BaseModel):
    status: str
    llm_configured: bool
