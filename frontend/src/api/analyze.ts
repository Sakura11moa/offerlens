import axios from "axios";
import type { AnalyzeRequest, AnalyzeResponse, ApiError } from "../types/analyze";

const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000",
  timeout: 30000,
});

export async function analyzeResume(payload: AnalyzeRequest): Promise<AnalyzeResponse> {
  try {
    const { data } = await http.post<AnalyzeResponse>("/api/analyze", payload);
    return data;
  } catch (error: unknown) {
    if (axios.isAxiosError(error)) {
      const serverData = error.response?.data as ApiError | undefined;
      const message = serverData?.error?.message || error.message || "Request failed";
      throw new Error(message);
    }
    throw new Error("Unexpected request error");
  }
}
