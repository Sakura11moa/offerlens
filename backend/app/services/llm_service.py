import json
from pathlib import Path

import httpx
from fastapi import HTTPException, status

from app.core.config import get_settings
from app.schemas import AnalyzeResponse


class LLMService:
    def __init__(self) -> None:
        self.settings = get_settings()

    @staticmethod
    def _load_prompt_template() -> str:
        prompt_file = Path(__file__).resolve().parent.parent / "prompts" / "resume_analysis_prompt.txt"
        return prompt_file.read_text(encoding="utf-8")

    @staticmethod
    def _resolve_chat_completions_url(base_url: str) -> str:
        cleaned = base_url.strip().rstrip("/")
        lowered = cleaned.lower()

        if lowered.endswith("/v1/chat/completions") or lowered.endswith("/chat/completions"):
            return cleaned

        if lowered.endswith("/v1"):
            return f"{cleaned}/chat/completions"

        # Compatibility fallback for providers that expose OpenAI API under /v1.
        return f"{cleaned}/v1/chat/completions"

    @staticmethod
    def _extract_json_content(raw_text: str) -> dict:
        text = raw_text.strip()

        if text.startswith("```"):
            lines = text.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            text = "\n".join(lines).strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Invalid JSON response from LLM",
            ) from exc

    async def analyze_resume(self, resume_text: str, job_description: str) -> AnalyzeResponse:
        if not self.settings.llm_api_key.strip():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="LLM not configured. Please set LLM_API_KEY.",
            )

        if not self.settings.llm_base_url.strip():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="LLM not configured. Please set LLM_BASE_URL.",
            )

        prompt_template = self._load_prompt_template()
        prompt = prompt_template.format(
            resume_text=resume_text.strip(),
            job_description=job_description.strip(),
        )

        payload = {
            "model": self.settings.llm_model,
            "messages": [
                {"role": "system", "content": "You are a strict JSON generator."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }

        headers = {
            "Authorization": f"Bearer {self.settings.llm_api_key}",
            "Content-Type": "application/json",
        }
        request_url = self._resolve_chat_completions_url(self.settings.llm_base_url)

        try:
            async with httpx.AsyncClient(timeout=self.settings.llm_timeout) as client:
                response = await client.post(
                    request_url,
                    json=payload,
                    headers=headers,
                )
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to call LLM service: {exc}",
            ) from exc

        if response.status_code >= 400:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"LLM service returned status {response.status_code}",
            )

        try:
            body = response.json()
            content = body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Unexpected LLM response format",
            ) from exc

        parsed = self._extract_json_content(content)

        try:
            return AnalyzeResponse.model_validate(parsed)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="LLM response does not match expected schema",
            ) from exc
