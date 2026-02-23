import { GenerationMode } from "@/types/image";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface GenerateRequest {
  prompt: string;
  mode: GenerationMode;
  model: string;
  sourceImage?: File | null;
}

export interface GenerationJob {
  job_id: string; // 작업 식별자
  id?: number; // DB 에셋 ID
  status: "pending" | "processing" | "completed" | "failed"; // 작업 상태
  result_url?: string; // 백엔드 원본 필드 (Snake Case)
  // resultUrl?: string; // 프론트엔드 사용 필드 (Camel Case)
  error?: string; // 에러 메시지
  created_at: string; // 생성 일시
  asset_type?: string; // 에셋 타입
}

export const generateAsset = async (
  req: GenerateRequest,
): Promise<{ job_id: string; status: GenerationJob["status"] }> => {
  console.log("[service/generation] generateAsset called", {
    API_BASE_URL,
    req,
  });

  const formData = new FormData();
  formData.append("prompt", req.prompt);
  formData.append("mode", req.mode);
  formData.append("model", req.model);

  if (req.sourceImage) {
    formData.append("source_image", req.sourceImage);
  }

  try {
    const url = `${API_BASE_URL}/api/assets/generate`;
    console.log(`[service/generation] POST to: ${url}`);
    const response = await fetch(url, {
      method: "POST",
      body: formData,
    });

    console.log("[service/generation] fetch response status:", response.status);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      console.error("[service/generation] fetch error data:", errorData);
      throw new Error(errorData.detail || "Failed to start generation job");
    }

    const data = await response.json();
    console.log("[service/generation] fetch success data:", data);
    return data;
  } catch (error) {
    console.error("[service/generation] fetch exception:", error);
    throw error;
  }
};

export const getJobStatus = async (jobId: string): Promise<GenerationJob> => {
  const url = `${API_BASE_URL}/api/assets/job/${jobId}`;
  console.log(`[service/generation] GET job status: ${url}`);
  const response = await fetch(url);

  if (!response.ok) {
    throw new Error("Failed to fetch job status");
  }

  const data = await response.json();
  // 백엔드의 대문자 상태값(PENDING 등)을 프론트엔드 소문자 형식으로 변환
  if (data.status) {
    data.status = data.status.toLowerCase();
  }
  return data;
};
