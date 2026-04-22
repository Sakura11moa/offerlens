from fastapi import APIRouter

from app.core.config import get_settings
from app.schemas import AnalyzeRequest, AnalyzeResponse, HealthResponse
from app.services.analyzer_service import AnalyzerService

router = APIRouter(prefix="/api", tags=["OfferLens"])
analyzer_service = AnalyzerService()


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(status="ok", llm_configured=settings.llm_enabled)


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    return await analyzer_service.analyze(request)
