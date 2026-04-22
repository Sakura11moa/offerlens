import axios from "axios";
import type { AnalyzeRequest, AnalyzeResponse, ApiError } from "../types/analyze";

const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000",
  timeout: 90000,
  validateStatus: () => true,
});

function isStringArray(value: unknown): value is string[] {
  return Array.isArray(value) && value.every((item) => typeof item === "string");
}

function isValidAnalyzeResponse(data: unknown): data is AnalyzeResponse {
  if (!data || typeof data !== "object") {
    return false;
  }

  const payload = data as Partial<AnalyzeResponse>;
  return (
    typeof payload.score === "number" &&
    isStringArray(payload.strengths) &&
    isStringArray(payload.weaknesses) &&
    isStringArray(payload.missing_keywords) &&
    isStringArray(payload.rewrite_suggestions) &&
    isStringArray(payload.interview_questions) &&
    typeof payload.summary === "string"
  );
}

function getFriendlyErrorMessage(error: unknown): string {
  if (!axios.isAxiosError(error)) {
    if (error instanceof Error && error.message) {
      return error.message;
    }
    return "请求异常，请稍后重试。";
  }

  if (error.code === "ECONNABORTED") {
    return "分析请求超时，请稍后重试。";
  }

  if (!error.response) {
    return "无法连接到服务，请检查网络或确认服务是否已启动。";
  }

  const serverData = error.response.data as ApiError | undefined;
  const serverMessage = serverData?.error?.message || "";

  if (error.response.status === 422) {
    return "输入内容不符合要求，请检查简历和岗位描述长度后重试。";
  }

  if (error.response.status === 503) {
    return "模型服务暂不可用，请检查模型配置或稍后再试。";
  }

  if (error.response.status >= 500) {
    return "分析服务暂时繁忙，请稍后再试。";
  }

  return serverMessage || "分析失败，请稍后重试。";
}

export async function analyzeResume(payload: AnalyzeRequest): Promise<AnalyzeResponse> {
  try {
    const response = await http.post("/api/analyze", payload);

    if (response.status !== 200) {
      throw new axios.AxiosError(
        "Request failed",
        undefined,
        response.config,
        response.request,
        response,
      );
    }

    if (!isValidAnalyzeResponse(response.data)) {
      throw new Error("分析结果格式异常，请稍后重试。");
    }

    return response.data;
  } catch (error: unknown) {
    throw new Error(getFriendlyErrorMessage(error));
  }
}
