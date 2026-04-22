from app.schemas import AnalyzeRequest, AnalyzeResponse
from app.services.llm_service import LLMService


class AnalyzerService:
    def __init__(self) -> None:
        self.llm_service = LLMService()

    async def analyze(self, request: AnalyzeRequest) -> AnalyzeResponse:
        return await self.llm_service.analyze_resume(
            resume_text=request.resume_text,
            job_description=request.job_description,
        )
