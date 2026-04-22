import axios from "axios";
import type { AnalyzeRequest, AnalyzeResponse, ApiError } from "../types/analyze";

const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000",
  timeout: 30000,
});

function getFriendlyErrorMessage(error: unknown): string {
  if (!axios.isAxiosError(error)) {
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
    return "输入内容不符合要求，请检查简历和岗位描述的长度后重试。";
  }

  if (error.response.status === 503) {
    return "模型服务暂不可用，请检查模型配置或稍后再试。";
  }

  if (error.response.status >= 500) {
    return "服务暂时繁忙，请稍后再试。";
  }

  return serverMessage || "分析失败，请稍后重试。";
}

export async function analyzeResume(payload: AnalyzeRequest): Promise<AnalyzeResponse> {
  try {
    const { data } = await http.post<AnalyzeResponse>("/api/analyze", payload);
    return data;
  } catch (error: unknown) {
    throw new Error(getFriendlyErrorMessage(error));
  }
}
