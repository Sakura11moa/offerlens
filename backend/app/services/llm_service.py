import asyncio
import json
import logging
import re
from pathlib import Path

import httpx

from app.core.config import get_settings
from app.schemas import AnalyzeResponse

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class LLMServiceError(Exception):
    def __init__(self, kind: str, message: str, retryable: bool = False) -> None:
        super().__init__(message)
        self.kind = kind
        self.message = message
        self.retryable = retryable


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

        return f"{cleaned}/v1/chat/completions"

    @staticmethod
    def _normalize_message_content(content: object) -> str:
        if isinstance(content, str):
            return content

        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    parts.append(str(item.get("text", "")))
                elif isinstance(item, str):
                    parts.append(item)
            return "".join(parts)

        return ""

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

        candidates = [text]
        first_brace = text.find("{")
        last_brace = text.rfind("}")
        if 0 <= first_brace < last_brace:
            candidates.append(text[first_brace : last_brace + 1])

        for candidate in candidates:
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                continue

        raise LLMServiceError(
            kind="invalid_json",
            message="上游模型返回内容格式异常，无法解析。",
            retryable=True,
        )

    @staticmethod
    def _coerce_string_list(value: object) -> list[str]:
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]

        if isinstance(value, str):
            parts = re.split(r"[\n\r]+|[;，,]", value)
            return [part.strip(" -*•\t") for part in parts if part.strip(" -*•\t")]

        return []

    @staticmethod
    def _coerce_score(value: object) -> int:
        if isinstance(value, int):
            return max(0, min(100, value))

        if isinstance(value, float):
            return max(0, min(100, int(round(value))))

        if isinstance(value, str):
            match = re.search(r"\d{1,3}", value)
            if match:
                return max(0, min(100, int(match.group(0))))

        return 0

    def _coerce_response_payload(self, parsed: object) -> dict:
        if not isinstance(parsed, dict):
            raise LLMServiceError(
                kind="invalid_payload",
                message="上游模型返回结构异常。",
                retryable=True,
            )

        return {
            "score": self._coerce_score(parsed.get("score")),
            "strengths": self._coerce_string_list(parsed.get("strengths")),
            "weaknesses": self._coerce_string_list(parsed.get("weaknesses")),
            "missing_keywords": self._coerce_string_list(parsed.get("missing_keywords")),
            "rewrite_suggestions": self._coerce_string_list(parsed.get("rewrite_suggestions")),
            "interview_questions": self._coerce_string_list(parsed.get("interview_questions")),
            "summary": str(parsed.get("summary") or "模型未返回完整总结，已使用基础逻辑补全。").strip(),
        }

    @staticmethod
    def _is_retryable_status(status_code: int) -> bool:
        return status_code in {408, 409, 425, 429, 500, 502, 503, 504}

    def _build_payload(self, prompt: str, compact: bool) -> dict:
        user_prompt = prompt
        payload = {
            "model": self.settings.llm_model,
            "messages": [
                {"role": "system", "content": "You are a strict JSON generator. Output valid Chinese JSON only."},
            ],
            "temperature": 0.1,
        }

        if compact:
            user_prompt += (
                "\n\nExtra retry constraint: keep output compact. "
                "Use concise bullet-like items and keep summary short."
            )
            payload["max_tokens"] = 700

        payload["messages"].append({"role": "user", "content": user_prompt})
        return payload

    async def _request_completion(self, request_url: str, headers: dict[str, str], prompt: str, compact: bool) -> str:
        payload = self._build_payload(prompt, compact=compact)

        try:
            async with httpx.AsyncClient(timeout=self.settings.llm_timeout_config) as client:
                response = await client.post(
                    request_url,
                    json=payload,
                    headers=headers,
                )
        except httpx.ConnectTimeout as exc:
            raise LLMServiceError(kind="connect_timeout", message="连接模型服务超时。", retryable=True) from exc
        except httpx.ReadTimeout as exc:
            raise LLMServiceError(kind="read_timeout", message="模型生成结果超时。", retryable=True) from exc
        except httpx.WriteTimeout as exc:
            raise LLMServiceError(kind="write_timeout", message="请求写入模型服务超时。", retryable=True) from exc
        except httpx.PoolTimeout as exc:
            raise LLMServiceError(kind="pool_timeout", message="连接池等待超时。", retryable=True) from exc
        except httpx.HTTPError as exc:
            raise LLMServiceError(kind="network_error", message="调用模型服务失败。", retryable=True) from exc

        if response.status_code >= 400:
            if self._is_retryable_status(response.status_code):
                raise LLMServiceError(
                    kind="upstream_retryable_status",
                    message=f"上游模型服务暂时不可用（{response.status_code}）。",
                    retryable=True,
                )
            raise LLMServiceError(
                kind="upstream_status",
                message=f"上游模型服务返回异常状态（{response.status_code}）。",
                retryable=False,
            )

        try:
            body = response.json()
            return self._normalize_message_content(body["choices"][0]["message"]["content"])
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise LLMServiceError(
                kind="unexpected_response",
                message="上游模型响应结构异常。",
                retryable=True,
            ) from exc

    async def analyze_resume(self, resume_text: str, job_description: str) -> AnalyzeResponse:
        if not self.settings.llm_api_key.strip() or not self.settings.llm_base_url.strip():
            raise LLMServiceError(
                kind="not_configured",
                message="模型配置未完成。",
                retryable=False,
            )

        prompt_template = self._load_prompt_template()
        prompt = prompt_template.format(
            resume_text=resume_text.strip(),
            job_description=job_description.strip(),
        )

        headers = {
            "Authorization": f"Bearer {self.settings.llm_api_key}",
            "Content-Type": "application/json",
        }
        request_url = self._resolve_chat_completions_url(self.settings.llm_base_url)

        total_attempts = self.settings.llm_total_attempts
        last_error: LLMServiceError | None = None

        for attempt in range(1, total_attempts + 1):
            compact = attempt == total_attempts and total_attempts > 1
            logger.warning(
                "Analyze stage=request_llm attempt=%s/%s compact=%s",
                attempt,
                total_attempts,
                compact,
            )

            try:
                content = await self._request_completion(request_url, headers, prompt, compact=compact)
                parsed = self._extract_json_content(content)
                normalized = self._coerce_response_payload(parsed)
                return AnalyzeResponse.model_validate(normalized)
            except LLMServiceError as exc:
                last_error = exc
                if exc.retryable and attempt < total_attempts:
                    backoff = max(0.0, float(self.settings.llm_retry_backoff)) * attempt
                    logger.warning(
                        "Analyze stage=retry reason=%s attempt=%s/%s backoff=%.2fs",
                        exc.kind,
                        attempt,
                        total_attempts,
                        backoff,
                    )
                    if backoff > 0:
                        await asyncio.sleep(backoff)
                    continue
                logger.warning(
                    "Analyze stage=llm_failed reason=%s retryable=%s attempt=%s/%s",
                    exc.kind,
                    exc.retryable,
                    attempt,
                    total_attempts,
                )
                break
            except Exception as exc:
                last_error = LLMServiceError(
                    kind="unexpected_exception",
                    message="模型分析过程出现异常。",
                    retryable=False,
                )
                logger.exception("Analyze stage=llm_unexpected_error err=%s", exc)
                break

        raise last_error or LLMServiceError(
            kind="unknown_failure",
            message="模型服务当前不可用。",
            retryable=False,
        )
