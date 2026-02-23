"use client";

import React, { useState, useCallback } from "react";
import { GenerateRequest } from "@/services/generation";
import { useGenerationJob } from "@/hooks/useGenerationJob";
import { GenerationInput } from "./GenerationInput";
import { GenerationMode } from "@/types/image";
import { ModelType } from "./ModelSelector";

import { useGenerationSessions } from "@/hooks/useGenerationSessions";
import { useRouter, useSearchParams } from "next/navigation";

// 1. 상태 객체화 (Props 최소화 및 확장성 확보)
export interface GenerationConfig {
  prompt: string;
  mode: GenerationMode;
  sourceImage: File | null;
}

// 모드별 예상 소요 시간 (ms)
const DURATION_MAP: Record<string, number> = {
  "text-to-image": 6000,
  "text-to-video": 25000,
  "image-to-video": 30000,
};

// 모드별 모델 매핑
const MODE_MODEL_MAP: Record<GenerationMode, ModelType> = {
  "text-to-image": "imagen-3.0-fast-generate-001",
  "text-to-video": "veo-3.0-fast-generate-001",
  "image-to-video": "veo-3.0-fast-generate-001",
};

export const GenerationContainer = ({ initialPrompt }: { initialPrompt?: string }) => {
  const { startJob, jobStatus, currentJob, error, isStarting } =
    useGenerationJob();

  // 1. 커스텀 훅을 통한 세션 관리 분리
  const { sessions, currentMode, updateConfig, clearPrompt } =
    useGenerationSessions(initialPrompt);

  const router = useRouter();
  const searchParams = useSearchParams();

  // 1.5. 결과창 가시성 상태 (한 번 활성화되면 유지)
  const [isResultVisible, setIsResultVisible] = useState(jobStatus !== 'idle');
  const [isSubmitting, setIsSubmitting] = useState(false);

  // URL 파라미터 초기화 함수
  const clearUrlParams = useCallback(() => {
    const params = new URLSearchParams(searchParams.toString());
    params.delete('q');
    params.delete('hybrid');
    router.push(`?${params.toString()}`, { scroll: false });
  }, [router, searchParams]);

  /**
   * TODO: 현재는 모드별 소스 이미지(File)를 메모리에 계속 유지하고 있습니다.
   * 서비스 모드가 늘어나거나 대용량 파일을 취급하게 될 경우,
   * 비활성화된 탭의 파일에 대해 URL.revokeObjectURL을 호출하거나
   * 상태를 명시적으로 해제하는 메모리 최적화 로직이 필요할 수 있습니다.
   */

  // 2. 현재 활성화된 모드의 설정 (부모-자식 간 Controlled 컴포넌트 패턴 지원)
  const config: GenerationConfig = React.useMemo(
    () => ({
      mode: currentMode,
      prompt: sessions[currentMode].prompt,
      sourceImage: sessions[currentMode].sourceImage,
    }),
    [currentMode, sessions],
  );

  // 3. Snapshot: 마지막 성공 시점의 설정 (재생성용)
  const [lastConfig, setLastConfig] = useState<GenerationConfig | null>(null);

  // 🚀 [Critical] 버튼 블로킹은 서버 요청 중(isStarting/isSubmitting)이거나 작업이 진행 중(pending/processing)일 때 모두 발생해야 함.
  const isLoading = isSubmitting || isStarting || jobStatus === 'pending' || jobStatus === 'processing';

  // 4. 단일 생성 함수 (유효성 검사 및 전송)
  const handleGenerate = useCallback(
    async (inputConfig?: GenerationConfig) => {
      const targetConfig = inputConfig || config;

      // 유효성 검사
      if (targetConfig.mode === "image-to-video" && !targetConfig.sourceImage) {
        console.warn(
          "[GenerationContainer] Image-to-video requires source image",
        );
        return;
      }
      if (
        targetConfig.mode !== "image-to-video" &&
        !targetConfig.prompt.trim()
      ) {
        console.warn("[GenerationContainer] Prompt is required");
        return;
      }

      // Snapshot 저장
      setLastConfig({ ...targetConfig });

      // ✨ 초기화 로직 제거 (완료 시점으로 이동)
      // if (!inputConfig) {
      //   clearPrompt();
      // }

      const request: GenerateRequest = {
        prompt: targetConfig.prompt,
        mode: targetConfig.mode,
        model: MODE_MODEL_MAP[targetConfig.mode],
        sourceImage: targetConfig.sourceImage,
      };

      console.log("[GenerationContainer] handleGenerate triggered", request);
      try {
        setIsSubmitting(true);
        // 생성이 시작되면 결과창(틀) 노출 활성화 및 URL 초기화
        setIsResultVisible(true);
        clearUrlParams();

        await startJob(request);
      } catch (e) {
        console.error("[GenerationContainer] Error in handleGenerate:", e);
        // 에러 발생 시에도 쿨다운은 유지됨 (의도적)
      } finally {
        setIsSubmitting(false);
      }
    },
    [config, startJob, clearUrlParams],
  );


  // ✨ [UX] 작업이 완료되거나 실패했을 때 텍스트 프롬프트 초기화
  React.useEffect(() => {
    if (jobStatus === "completed" || jobStatus === "failed") {
      clearPrompt();
    }
  }, [jobStatus, clearPrompt]);

  return (
    <div className="w-[85%] max-w-[1700px] mx-auto pt-8">
      <GenerationInput
        config={config}
        onConfigChange={updateConfig}
        onGenerate={() => handleGenerate()}
        isLoading={isLoading}
        expectedDuration={DURATION_MAP[config.mode] || 5000}
      />
    </div>
  );
};
