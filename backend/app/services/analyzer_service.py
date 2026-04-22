import logging
import re
from typing import Iterable

from fastapi import HTTPException

from app.schemas import AnalyzeRequest, AnalyzeResponse
from app.services.llm_service import LLMService, LLMServiceError


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

TRIM_CHARS = "\uff0c\u3002\uff1b;\uff1a:\u3001 "
SUMMARY_ENDINGS = ("\u3002", "\uff1b", "\uff0c")


class AnalyzerService:
    def __init__(self) -> None:
        self.llm_service = LLMService()

    async def analyze(self, request: AnalyzeRequest) -> AnalyzeResponse:
        logger.warning(
            "Analyze stage=start resume_len=%s jd_len=%s",
            len(request.resume_text),
            len(request.job_description),
        )

        try:
            llm_response = await self.llm_service.analyze_resume(
                resume_text=request.resume_text,
                job_description=request.job_description,
            )
            logger.warning("Analyze stage=llm_success")
            return self._post_process_response(llm_response, request)
        except LLMServiceError as exc:
            logger.warning(
                "Analyze stage=fallback_triggered reason=%s retryable=%s",
                exc.kind,
                exc.retryable,
            )
            fallback = self._build_rule_based_response(request, reason=exc.kind)
            result = self._post_process_response(fallback, request)
            logger.warning("Analyze stage=fallback_success")
            return result
        except Exception as exc:
            logger.exception("Analyze stage=failed_unrecoverable err=%s", exc)
            raise HTTPException(status_code=500, detail="分析服务暂不可用，请稍后重试。") from exc

    def _build_rule_based_response(self, request: AnalyzeRequest, reason: str) -> AnalyzeResponse:
        jd_keywords = self._extract_jd_keywords(request.job_description, [])
        matched_keywords = self._match_keywords(jd_keywords, request.resume_text)
        resume_lower = request.resume_text.lower()
        missing_keywords = [kw for kw in jd_keywords if kw.lower() not in resume_lower][:8]
        has_metrics = self._has_quantified_results(request.resume_text)
        has_project_evidence = self._has_project_evidence(request.resume_text)

        score = self._rule_based_score(
            matched_count=len(matched_keywords),
            keyword_count=max(1, len(jd_keywords)),
            missing_count=len(missing_keywords),
            has_metrics=has_metrics,
            has_project_evidence=has_project_evidence,
        )

        strengths = self._build_fallback_strengths(matched_keywords)[:4]
        weaknesses = self._build_fallback_weaknesses(missing_keywords, has_metrics, has_project_evidence)[:4]
        rewrite_suggestions = self._build_fallback_rewrite_suggestions(matched_keywords, missing_keywords, has_metrics)[:5]
        interview_questions = self._build_fallback_interview_questions(matched_keywords, missing_keywords, has_metrics)[:6]

        reason_text_map = {
            "read_timeout": "\u6a21\u578b\u54cd\u5e94\u8d85\u65f6",
            "connect_timeout": "\u6a21\u578b\u8fde\u63a5\u8d85\u65f6",
            "upstream_retryable_status": "\u6a21\u578b\u670d\u52a1\u6682\u4e0d\u7a33\u5b9a",
            "not_configured": "\u6a21\u578b\u914d\u7f6e\u672a\u5b8c\u6210",
        }
        reason_text = reason_text_map.get(reason, "\u6a21\u578b\u670d\u52a1\u6682\u65f6\u4e0d\u53ef\u7528")

        summary = (
            f"\u4f60\u7684\u7b80\u5386\u4e0e\u5c97\u4f4d\u5b58\u5728\u4e00\u5b9a\u5339\u914d\u5173\u7cfb\uff0c"
            f"\u4f46\u5f53\u524d\u4e3a\u57fa\u7840\u89c4\u5219\u5206\u6790\uff08{reason_text}\uff09\u3002"
            "\u5efa\u8bae\u4f18\u5148\u8865\u5f3a\u7f3a\u5931\u5173\u952e\u8bcd\u548c\u91cf\u5316\u6210\u679c\u8868\u8fbe\uff0c"
            "\u7a0d\u540e\u518d\u6b21\u53d1\u8d77\u5206\u6790\u4ee5\u83b7\u53d6\u66f4\u7ec6\u5316\u7684 AI \u89e3\u8bfb\u3002"
        )

        return AnalyzeResponse(
            score=score,
            strengths=strengths or ["\u7b80\u5386\u4e2d\u5df2\u6709\u90e8\u5206\u53ef\u8fc1\u79fb\u80cc\u666f\uff0c\u4f46\u4ecd\u9700\u66f4\u76f4\u63a5\u5bf9\u9f50 JD \u6838\u5fc3\u8981\u6c42\u3002"],
            weaknesses=weaknesses or ["\u7b80\u5386\u4e0e\u5c97\u4f4d\u4e4b\u95f4\u8fd8\u5b58\u5728\u4e00\u5b9a\u4fe1\u606f\u7f3a\u53e3\uff0c\u5efa\u8bae\u8865\u5145\u76f8\u5173\u9879\u76ee\u4e0e\u6210\u679c\u3002"],
            missing_keywords=missing_keywords[:8] or ["\u8bf7\u8865\u5145\u4e0e JD \u5f3a\u76f8\u5173\u7684\u6280\u80fd\u5173\u952e\u8bcd"],
            rewrite_suggestions=rewrite_suggestions,
            interview_questions=interview_questions,
            summary=summary,
        )

    @staticmethod
    def _rule_based_score(
        matched_count: int,
        keyword_count: int,
        missing_count: int,
        has_metrics: bool,
        has_project_evidence: bool,
    ) -> int:
        ratio = matched_count / max(1, keyword_count)

        if ratio >= 0.75:
            score = 84
        elif ratio >= 0.55:
            score = 72
        elif ratio >= 0.35:
            score = 60
        elif ratio >= 0.2:
            score = 48
        else:
            score = 35

        if missing_count >= 6:
            score -= 12
        elif missing_count >= 4:
            score -= 8
        elif missing_count >= 2:
            score -= 4

        if not has_metrics:
            score -= 6
        if not has_project_evidence:
            score -= 5

        return max(15, min(95, score))

    def _post_process_response(self, response: AnalyzeResponse, request: AnalyzeRequest) -> AnalyzeResponse:
        strengths = self._clean_list(response.strengths, limit=4, max_length=70)
        weaknesses = self._clean_list(response.weaknesses, limit=4, max_length=70)
        missing_keywords = self._clean_list(response.missing_keywords, limit=8, max_length=24)
        rewrite_suggestions = self._clean_list(response.rewrite_suggestions, limit=5, max_length=90)
        interview_questions = self._clean_list(response.interview_questions, limit=6, max_length=90)
        summary = self._clean_summary(response.summary)

        jd_keywords = self._extract_jd_keywords(request.job_description, missing_keywords)
        matched_keywords = self._match_keywords(jd_keywords, request.resume_text)
        has_metrics = self._has_quantified_results(request.resume_text)
        has_project_evidence = self._has_project_evidence(request.resume_text)

        if not strengths:
            strengths = self._build_fallback_strengths(matched_keywords)

        if not weaknesses:
            weaknesses = self._build_fallback_weaknesses(missing_keywords, has_metrics, has_project_evidence)

        if len(rewrite_suggestions) < 3:
            rewrite_suggestions = self._merge_with_fallbacks(
                rewrite_suggestions,
                self._build_fallback_rewrite_suggestions(matched_keywords, missing_keywords, has_metrics),
                limit=5,
            )

        if len(interview_questions) < 4:
            interview_questions = self._merge_with_fallbacks(
                interview_questions,
                self._build_fallback_interview_questions(matched_keywords, missing_keywords, has_metrics),
                limit=6,
            )

        if not summary:
            summary = self._build_fallback_summary(
                score=response.score,
                matched_keywords=matched_keywords,
                missing_keywords=missing_keywords,
                has_metrics=has_metrics,
            )

        adjusted_score = self._adjust_score(
            original_score=response.score,
            matched_keywords=matched_keywords,
            jd_keywords=jd_keywords,
            missing_keywords=missing_keywords,
            weaknesses=weaknesses,
            has_metrics=has_metrics,
            has_project_evidence=has_project_evidence,
        )

        return AnalyzeResponse(
            score=adjusted_score,
            strengths=strengths,
            weaknesses=weaknesses,
            missing_keywords=missing_keywords,
            rewrite_suggestions=rewrite_suggestions,
            interview_questions=interview_questions,
            summary=summary,
        )

    @staticmethod
    def _clean_item(item: str, max_length: int) -> str:
        text = re.sub(r"\s+", " ", str(item or "")).strip()
        text = re.sub(r"^[\-\*\d\.\)\u2022\s]+", "", text)
        text = text.strip(TRIM_CHARS)
        if len(text) > max_length:
            text = text[: max_length - 1].rstrip(TRIM_CHARS) + "\u2026"
        return text

    def _clean_list(self, items: Iterable[str], limit: int, max_length: int) -> list[str]:
        cleaned: list[str] = []
        seen: set[str] = set()

        for raw_item in items:
            item = self._clean_item(raw_item, max_length=max_length)
            if not item:
                continue

            normalized = item.lower()
            if normalized in seen:
                continue

            seen.add(normalized)
            cleaned.append(item)
            if len(cleaned) >= limit:
                break

        return cleaned

    @staticmethod
    def _clean_summary(summary: str) -> str:
        text = re.sub(r"\s+", " ", str(summary or "")).strip()
        text = text.strip(TRIM_CHARS)
        if len(text) > 120:
            truncated = text[:120]
            last_cut = max(
                truncated.rfind(SUMMARY_ENDINGS[0]),
                truncated.rfind(SUMMARY_ENDINGS[1]),
                truncated.rfind(SUMMARY_ENDINGS[2]),
            )
            text = truncated[: last_cut + 1] if last_cut >= 30 else truncated.rstrip(TRIM_CHARS) + SUMMARY_ENDINGS[0]
        return text

    @staticmethod
    def _extract_jd_keywords(job_description: str, missing_keywords: list[str]) -> list[str]:
        english_tokens = re.findall(r"[A-Za-z][A-Za-z0-9+.#/-]{1,24}", job_description)
        stopwords = {"and", "with", "for", "the", "you", "will", "from", "that", "this", "have"}

        keywords: list[str] = []
        seen: set[str] = set()

        for token in english_tokens:
            normalized = token.lower()
            if normalized in stopwords or len(token) < 2:
                continue
            if normalized not in seen:
                seen.add(normalized)
                keywords.append(token)

        for keyword in missing_keywords:
            normalized = keyword.lower()
            if normalized not in seen:
                seen.add(normalized)
                keywords.append(keyword)

        return keywords[:12]

    @staticmethod
    def _match_keywords(keywords: list[str], resume_text: str) -> list[str]:
        resume_lower = resume_text.lower()
        matched: list[str] = []
        seen: set[str] = set()

        for keyword in keywords:
            normalized = keyword.lower()
            if normalized in resume_lower and normalized not in seen:
                matched.append(keyword)
                seen.add(normalized)

        return matched

    @staticmethod
    def _has_quantified_results(text: str) -> bool:
        return bool(
            re.search(
                r"\d+(\.\d+)?\s*(%|\uff05|\u500d|\u4e2a|\u6b21|\u5e74|\u6708|\u5468|\u5929|\u4eba|\u9879|ms|\u79d2|\u4e07\u5143|\u4e07|\u5343)",
                text,
            )
        )

    @staticmethod
    def _has_project_evidence(text: str) -> bool:
        return bool(
            re.search(
                "\u9879\u76ee|\u8d1f\u8d23|\u4e3b\u5bfc|\u642d\u5efa|\u4f18\u5316|\u4e0a\u7ebf|\u843d\u5730|\u6539\u9020|\u8bbe\u8ba1|\u5f00\u53d1|\u4ea4\u4ed8|\u63a8\u52a8|\u534f\u4f5c|\u5b9e\u73b0|project|built|led|designed",
                text,
                re.IGNORECASE,
            )
        )

    @staticmethod
    def _build_fallback_strengths(matched_keywords: list[str]) -> list[str]:
        if matched_keywords:
            top_keywords = "\u3001".join(matched_keywords[:3])
            return [f"\u7b80\u5386\u4e2d\u5df2\u4f53\u73b0 {top_keywords} \u76f8\u5173\u7ecf\u9a8c\uff0c\u4e0e JD \u7684\u6838\u5fc3\u6280\u80fd\u8981\u6c42\u5b58\u5728\u76f4\u63a5\u91cd\u5408\u3002"]
        return ["\u7b80\u5386\u4e2d\u6709\u4e00\u5b9a\u76f8\u5173\u80cc\u666f\uff0c\u4f46\u5f53\u524d\u80fd\u76f4\u63a5\u5bf9\u5e94 JD \u6838\u5fc3\u8981\u6c42\u7684\u8bc1\u636e\u4ecd\u7136\u6709\u9650\u3002"]

    @staticmethod
    def _build_fallback_weaknesses(
        missing_keywords: list[str],
        has_metrics: bool,
        has_project_evidence: bool,
    ) -> list[str]:
        weaknesses: list[str] = []

        if missing_keywords:
            weaknesses.append(f"JD \u91cd\u70b9\u5f3a\u8c03\u7684 {missing_keywords[0]} \u5728\u7b80\u5386\u4e2d\u6ca1\u6709\u88ab\u660e\u786e\u4f53\u73b0\u3002")
        if len(missing_keywords) > 1:
            weaknesses.append(f"\u9664 {missing_keywords[0]} \u5916\uff0c{missing_keywords[1]} \u7b49\u5173\u952e\u8bcd\u4e5f\u4f1a\u5f71\u54cd\u521d\u7b5b\u5339\u914d\u5ea6\u3002")
        if not has_metrics:
            weaknesses.append("\u7b80\u5386\u7f3a\u5c11\u91cf\u5316\u6210\u679c\uff0c\u5bb9\u6613\u8ba9\u9879\u76ee\u4ef7\u503c\u548c\u4e1a\u52a1\u5f71\u54cd\u529b\u663e\u5f97\u4e0d\u591f\u5177\u4f53\u3002")
        if not has_project_evidence:
            weaknesses.append("\u7b80\u5386\u7f3a\u5c11\u5b8c\u6574\u9879\u76ee\u573a\u666f\u63cf\u8ff0\uff0c\u96be\u4ee5\u652f\u6491\u5c97\u4f4d\u8981\u6c42\u7684\u5b9e\u9645\u843d\u5730\u80fd\u529b\u5224\u65ad\u3002")

        return weaknesses[:4] or ["\u7b80\u5386\u4e0e\u5c97\u4f4d\u4ecd\u5b58\u5728\u4e00\u4e9b\u4fe1\u606f\u7f3a\u53e3\uff0c\u5efa\u8bae\u8865\u5145\u66f4\u5177\u4f53\u7684\u9879\u76ee\u4e0e\u6210\u679c\u63cf\u8ff0\u3002"]

    @staticmethod
    def _build_fallback_rewrite_suggestions(
        matched_keywords: list[str],
        missing_keywords: list[str],
        has_metrics: bool,
    ) -> list[str]:
        suggestions: list[str] = []

        if matched_keywords:
            suggestions.append(
                f"\u628a\u73b0\u6709\u7ecf\u5386\u6539\u5199\u6210\u201c\u57fa\u4e8e {matched_keywords[0]} \u5b8c\u6210\u4efb\u52a1 + \u89e3\u51b3\u95ee\u9898 + \u53d6\u5f97\u7ed3\u679c\u201d\uff0c\u5f31\u5316\u804c\u8d23\u7f57\u5217\u3002"
            )
        if not has_metrics:
            suggestions.append("\u4e3a\u91cd\u70b9\u9879\u76ee\u8865\u5145\u91cf\u5316\u6307\u6807\uff0c\u4f8b\u5982\u6548\u7387\u63d0\u5347\u3001\u6210\u672c\u4e0b\u964d\u6216\u8d28\u91cf\u6307\u6807\u6539\u5584\u3002")
        if missing_keywords:
            suggestions.append(
                f"\u5982\u679c\u4f60\u505a\u8fc7 {missing_keywords[0]} \u76f8\u5173\u5de5\u4f5c\uff0c\u5efa\u8bae\u5728\u9879\u76ee\u7ecf\u5386\u4e2d\u5355\u72ec\u5199\u51fa\u573a\u666f\u3001\u52a8\u4f5c\u548c\u7ed3\u679c\u3002"
            )
        if len(missing_keywords) > 1:
            suggestions.append(
                f"\u53ef\u5c06\u201c\u8d1f\u8d23\u5f00\u53d1/\u7ef4\u62a4\u201d\u6539\u5199\u4e3a\u201c\u56f4\u7ed5 {missing_keywords[1]} \u9700\u6c42\u5b8c\u6210\u8bbe\u8ba1\u3001\u5b9e\u73b0\u4e0e\u8054\u8c03\u201d\u3002"
            )
        suggestions.append("\u5c06\u6bcf\u6bb5\u7ecf\u5386\u5c3d\u91cf\u5199\u6210\u201c\u80cc\u666f-\u52a8\u4f5c-\u7ed3\u679c\u201d\u4e09\u6bb5\u5f0f\uff0c\u63d0\u9ad8\u521d\u7b5b\u901a\u8fc7\u7387\u3002")

        return suggestions[:5]

    @staticmethod
    def _build_fallback_interview_questions(
        matched_keywords: list[str],
        missing_keywords: list[str],
        has_metrics: bool,
    ) -> list[str]:
        questions: list[str] = []

        for keyword in matched_keywords[:2]:
            questions.append(f"\u4f60\u7b80\u5386\u4e2d\u63d0\u5230\u4e86 {keyword} \u7ecf\u9a8c\uff0c\u8bf7\u7ed3\u5408\u4e00\u4e2a\u9879\u76ee\u8bf4\u660e\u4f60\u7684\u8bbe\u8ba1\u4e0e\u843d\u5730\u8fc7\u7a0b\u3002")

        for keyword in missing_keywords[:2]:
            questions.append(f"\u8be5\u5c97\u4f4d\u5f3a\u8c03 {keyword}\uff0c\u5982\u679c\u9762\u8bd5\u5b98\u8ffd\u95ee\u4f60\u7684\u5b9e\u8df5\u7ecf\u5386\uff0c\u4f60\u4f1a\u600e\u4e48\u56de\u7b54\uff1f")

        if not has_metrics:
            questions.append("\u5982\u679c\u9762\u8bd5\u5b98\u8981\u6c42\u4f60\u7528\u6570\u636e\u8bc1\u660e\u9879\u76ee\u6548\u679c\uff0c\u4f60\u51c6\u5907\u7528\u54ea\u4e9b\u6307\u6807\u6765\u8bf4\u660e\uff1f")

        questions.append("\u5982\u679c\u8ba9\u4f60\u9488\u5bf9\u8be5\u5c97\u4f4d\u6700\u6838\u5fc3\u7684\u8981\u6c42\u4e3e\u4f8b\uff0c\u4f60\u4f1a\u4f18\u5148\u8bb2\u54ea\u6bb5\u7ecf\u5386\uff1f")
        return questions[:6]

    @staticmethod
    def _build_fallback_summary(
        score: int,
        matched_keywords: list[str],
        missing_keywords: list[str],
        has_metrics: bool,
    ) -> str:
        if score >= 75:
            return "\u4f60\u4e0e\u5c97\u4f4d\u6574\u4f53\u5339\u914d\u5ea6\u8f83\u9ad8\uff0c\u5efa\u8bae\u7ee7\u7eed\u5f3a\u5316\u9879\u76ee\u6210\u679c\u4e0e\u5173\u952e\u8bcd\u7684\u76f4\u63a5\u8868\u8fbe\u3002"
        if matched_keywords:
            missing_text = f"\uff0c\u5c24\u5176\u662f {missing_keywords[0]}" if missing_keywords else ""
            metric_text = "\uff0c\u5e76\u8865\u5145\u91cf\u5316\u6210\u679c" if not has_metrics else ""
            return f"\u4f60\u4e0e\u5c97\u4f4d\u6709\u4e00\u5b9a\u5339\u914d\uff0c\u4f46\u5b58\u5728\u5173\u952e\u7f3a\u53e3{missing_text}\u3002\u5efa\u8bae\u4f18\u5148\u8865\u5f3a\u76f8\u5173\u9879\u76ee\u8bc1\u636e{metric_text}\u3002"
        return "\u4f60\u4e0e\u5c97\u4f4d\u7684\u76f4\u63a5\u5339\u914d\u5ea6\u6709\u9650\uff0c\u5efa\u8bae\u5148\u8865\u8db3\u6838\u5fc3\u6280\u80fd\u5173\u952e\u8bcd\u548c\u5bf9\u5e94\u9879\u76ee\u7ecf\u5386\u3002"

    def _merge_with_fallbacks(self, current: list[str], fallbacks: list[str], limit: int) -> list[str]:
        merged = list(current)
        seen = {item.lower() for item in merged}

        for item in fallbacks:
            normalized = item.lower()
            if normalized in seen:
                continue
            merged.append(item)
            seen.add(normalized)
            if len(merged) >= limit:
                break

        return merged

    @staticmethod
    def _adjust_score(
        original_score: int,
        matched_keywords: list[str],
        jd_keywords: list[str],
        missing_keywords: list[str],
        weaknesses: list[str],
        has_metrics: bool,
        has_project_evidence: bool,
    ) -> int:
        adjusted = original_score
        keyword_count = max(len(jd_keywords), 1)
        match_ratio = len(matched_keywords) / keyword_count

        if match_ratio < 0.2:
            adjusted = min(adjusted, 42)
        elif match_ratio < 0.35:
            adjusted = min(adjusted, 56)
        elif match_ratio < 0.5:
            adjusted = min(adjusted, 68)
        elif match_ratio < 0.7:
            adjusted = min(adjusted, 80)
        else:
            adjusted = min(adjusted, 93)

        if len(missing_keywords) >= 5:
            adjusted -= 10
        elif len(missing_keywords) >= 3:
            adjusted -= 5

        if len(weaknesses) >= 4:
            adjusted -= 4

        if not has_metrics:
            adjusted -= 6

        if not has_project_evidence:
            adjusted -= 5

        return max(15, min(100, adjusted))


