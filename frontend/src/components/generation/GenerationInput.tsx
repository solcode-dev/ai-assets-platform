"use client";

import React, { memo, useCallback } from 'react';
import { Sparkles, Video, Image as ImageIcon, Check } from 'lucide-react';
import { useTaskStore } from '@/stores/useTaskStore';
import { TextPromptInput } from './TextPromptInput';
import { ImageUploader } from './ImageUploader';
import { ModelSelector, ModelType } from './ModelSelector';
import { GenerationMode } from '@/types/image';
import { GenerationConfig } from './GenerationContainer';
import { useQuotaStore } from '@/stores/useQuotaStore';
import { useFakeProgress } from '@/hooks/useFakeProgress';
import { AnimatePresence, motion } from 'framer-motion';

import { useRouter, useSearchParams } from 'next/navigation';
import { useDebouncedCallback } from 'use-debounce';

// 테크니컬 로그 메시지 정의 (from GenerationResult)
const LOG_MESSAGES = {
  image: [
    { range: [0, 20], text: "프롬프트 의미 구조 분석 중..." },
    { range: [20, 50], text: "잠재 공간(Latent Space) 샘플링..." },
    { range: [50, 80], text: "픽셀 단위 세부 텍스트 렌더링..." },
    { range: [80, 100], text: "최종 결과물의 노이즈 제거..." },
  ],
  video: [
    { range: [0, 20], text: "시간적 문맥(Temporal Context) 파싱..." },
    { range: [20, 50], text: "키프레임 생성 및 모션 벡터 계산..." },
    { range: [50, 80], text: "프레임 보간 및 일관성 확보..." },
    { range: [80, 100], text: "비디오 인코딩 중..." },
  ]
};

interface GenerationInputProps {
  config: GenerationConfig;
  onConfigChange: (config: GenerationConfig) => void;
  onGenerate: () => void;
  isLoading: boolean;
  expectedDuration?: number; // 🆕 추가
}

type ModeConfigItem = {
  label: string;
  icon: React.ReactNode;
  model: ModelType;
  description: string;
};

// MODE_CONFIG 외부 선언 (메모리 최적화)
const MODE_CONFIG: Record<GenerationMode, ModeConfigItem> = {
  "text-to-image": {
    label: "Text to Image",
    icon: <ImageIcon size={18} />,
    model: "imagen-3.0-fast-generate-001",
    description: "상상하는 이미지를 상세히 묘사하세요. 고품질 AI 아트를 바로 완성할 수 있습니다.",
  },
  "text-to-video": {
    label: "Text to Video",
    icon: <Video size={18} />,
    model: "veo-3.0-fast-generate-001",
    description: "아이디어를 입력하여 상상 속 장면을 생생한 고해상도 영상으로 구현해 보세요.",
  },
  "image-to-video": {
    label: "Image to Video",
    icon: <Sparkles size={18} />,
    model: "veo-3.0-fast-generate-001",
    description: "정적인 이미지에 자연스러운 움직임을 더해 생명력 넘치는 비디오를 제작할 수 있습니다.",
  },
};

// React.memo 적용: props 변경 시에만 리렌더링
export const GenerationInput = memo(function GenerationInput({ 
  config, 
  onConfigChange, 
  onGenerate, 
  isLoading,
  expectedDuration = 4000
}: GenerationInputProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const isOverLimit = useQuotaStore((state) => state.isOverLimit);
  
  // Progress Logic
  const progress = useFakeProgress({ 
    isLoading, 
    expectedDuration 
  });

  // Log Message Logic
  const isVideo = config.mode.includes('video');
  const logs = isVideo ? LOG_MESSAGES.video : LOG_MESSAGES.image;
  
  const currentLog = isLoading 
    ? (logs.find(log => progress >= log.range[0] && progress < log.range[1])?.text || logs[logs.length - 1].text)
    : "";


  const isHybrid = searchParams.get('hybrid') !== 'false';

  const updateUrlParams = useCallback((key: string, value?: string | null) => {
    const params = new URLSearchParams(searchParams.toString());
    
    // 값이 없거나, 빈 문자열이거나, 실수로 들어온 'undefined' 문자열인 경우 파라미터 삭제
    if (!value || value === 'undefined' || value.trim() === '') {
      params.delete(key);
    } else {
      params.set(key, value);
    }
    
    router.push(`?${params.toString()}`, { scroll: false });
  }, [router, searchParams]);

  // 검색 디바운싱: 500ms (생성 프롬프트 입력과 검색 경험 조율)
  const debouncedSearch = useDebouncedCallback((value: string) => {
    updateUrlParams('q', value);
  }, 500);
  
  const handleModeChange = useCallback((mode: GenerationMode) => {
    if (mode !== config.mode) {
      onConfigChange({
        ...config,
        mode,
      });
    }
  }, [config, onConfigChange]);

  const handlePromptChange = useCallback((prompt: string) => {
    onConfigChange({ ...config, prompt });
    debouncedSearch(prompt); // 프롬프트 변경 시 자동으로 검색 트리거
  }, [config, onConfigChange, debouncedSearch]);

  const handleImageChange = useCallback((file: File | null) => {
    onConfigChange({ ...config, sourceImage: file });
  }, [config, onConfigChange]);

  const handleHybridToggle = () => {
    updateUrlParams('hybrid', isHybrid ? 'false' : 'true');
  };

  // 유효성 검사 로직
  const isFormValid = (() => {
    if (config.mode === 'image-to-video') {
      return !!config.sourceImage;
    }
    return !!config.prompt.trim();
  })();

  const handleSubmit = useCallback(() => {
    if (!isFormValid || isLoading || isOverLimit) {
      return;
    }
    onGenerate();
  }, [isFormValid, isLoading, isOverLimit, onGenerate]);

  return (
    <div className="w-full mx-auto bg-white rounded-2xl shadow-xl border border-gray-100 overflow-hidden transition-all hover:shadow-2xl">
      {/* 1. Mode Tabs */}
      <div className="flex flex-col sm:flex-row border-b border-gray-100 bg-gray-50/50 p-1 gap-1 sm:gap-0">
        {(Object.keys(MODE_CONFIG) as GenerationMode[]).map((mode) => (
          <button
            key={mode}
            onClick={() => handleModeChange(mode)}
            disabled={isLoading}
            className={`
              flex items-center gap-2 flex-1 justify-center py-3 sm:py-2.5 text-sm font-medium rounded-xl transition-all
              ${config.mode === mode 
                ? 'bg-white text-blue-600 shadow-sm border border-gray-200/50' 
                : 'text-gray-500 hover:bg-gray-100 hover:text-gray-700'
              }
              ${isLoading ? "opacity-50 cursor-not-allowed" : ""}
            `}
          >
            {MODE_CONFIG[mode].icon}
            {MODE_CONFIG[mode].label}
          </button>
        ))}
      </div>

      {/* 2. Input Area (모드 전환 시 리렌더링 및 트랜지션 적용) */}
      <div 
        key={config.mode} 
        className="p-6 space-y-6 animate-in fade-in duration-500 fill-mode-both"
      >
        {/* 설명 및 모델 선택 / 하이브리드 토글 */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <p className="text-sm text-gray-500">
              {MODE_CONFIG[config.mode].description}
            </p>
            <div className="w-px h-4 bg-gray-200" />
            <div className="relative group/tooltip flex items-center gap-1.5 focus:outline-none" tabIndex={0}>
              <span className={`text-[10px] font-bold uppercase tracking-tight ${isHybrid ? 'text-blue-600' : 'text-gray-400'}`}>Hybrid Search</span>
              <svg 
                xmlns="http://www.w3.org/2000/svg" 
                width="13" 
                height="13" 
                viewBox="0 0 24 24" 
                fill="none" 
                stroke="currentColor" 
                strokeWidth="2.5" 
                strokeLinecap="round" 
                strokeLinejoin="round" 
                className="text-gray-400 group-hover/tooltip:text-blue-500 transition-colors cursor-help"
              >
                <circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><path d="M12 17h.01"/>
              </svg>
              
              {/* CSS Tooltip - 위치를 아래쪽(top-full)으로 변경하여 잘림 방지 */}
              <div className="absolute top-full left-1/2 -translate-x-1/2 mt-2 w-64 p-3 bg-gray-900 text-white text-[11px] leading-relaxed rounded-xl shadow-2xl opacity-0 invisible group-hover/tooltip:opacity-100 group-hover/tooltip:visible transition-all duration-200 z-50 pointer-events-none">
                <p className="font-bold text-blue-400 mb-1 text-center">검색 방식 안내</p>
                <div className="space-y-1.5 border-t border-gray-800 pt-2">
                  <p className="text-gray-300">• <span className="text-white font-semibold">하이브리드</span>: 키워드 매칭과 의미 검색의 종합 순위 (복합 점수로 % 표기 불가)</p>
                  <p className="text-gray-300">• <span className="text-white font-semibold">벡터 전용</span>: 의미 중심 일치율 측정 (% 표시 가능)</p>
                </div>
                {/* 말꼬리 아이콘 - 위쪽으로 방향 변경 */}
                <div className="absolute bottom-full left-1/2 -translate-x-1/2 -mb-1 border-4 border-transparent border-b-gray-900" />
              </div>
            </div>
            <button 
              onClick={handleHybridToggle}
              className={`w-8 h-4.5 rounded-full transition-all relative shadow-inner cursor-pointer ${isHybrid ? 'bg-blue-600' : 'bg-gray-200'}`}
            >
              <div className={`absolute top-0.5 w-3.5 h-3.5 bg-white rounded-full shadow-md transition-all ${isHybrid ? 'left-4' : 'left-0.5'}`} />
            </button>
          </div>
          <ModelSelector 
            currentModel={MODE_CONFIG[config.mode].model} 
            disabled={isLoading}
          />
        </div>

        {/* 텍스트 입력 (이제 검색 바 역할도 수행) */}
        <div className="space-y-2">
          <label className="text-xs font-semibold text-gray-400 uppercase tracking-wider ml-1">
            Prompt & Real-time Search
          </label>
          <TextPromptInput 
            value={config.prompt}
            onChange={handlePromptChange}
            disabled={isLoading}
            placeholder={
              config.mode === 'text-to-image' ? "생성하고 싶은 이미지를 묘사하세요. 유사한 에셋이 아래에 실시간으로 표시됩니다..." :
              config.mode === 'text-to-video' ? "A drone shot of a waterfall in a tropical jungle..." :
              "Describe how you want to animate this image (optional)..."
            }
          />
        </div>

        {/* 이미지 업로드 */}
        {config.mode === 'image-to-video' && (
          <div className="space-y-2 animate-in fade-in slide-in-from-top-4 duration-300">
            <label className="text-xs font-semibold text-gray-400 uppercase tracking-wider ml-1">Source Image</label>
            <ImageUploader 
              selectedFile={config.sourceImage}
              onFileSelect={handleImageChange}
              disabled={isLoading}
            />
          </div>
        )}

        {/* 3. Action Buttons & Settings */}
        <div className="flex items-center justify-between pt-2 h-[52px]">
          {/* Progress Indicator (Left Side) */}
          <div className="flex-1 pr-6">
            <AnimatePresence>
              {isLoading && (
                <motion.div
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -10 }}
                  className="w-full max-w-md"
                >
                  <div className="flex justify-between items-center mb-1.5">
                    <span className="text-xs font-medium text-blue-600 truncate max-w-[200px] sm:max-w-xs">{currentLog}</span>
                    <span className="text-[10px] font-bold text-gray-400">{Math.round(progress)}%</span>
                  </div>
                  <div className="h-1.5 w-full bg-gray-100 rounded-full overflow-hidden">
                    <motion.div 
                      className="h-full bg-linear-to-r from-blue-500 to-indigo-500"
                      initial={{ width: 0 }}
                      animate={{ width: `${progress}%` }}
                      transition={{ ease: "linear", duration: 0.2 }}
                    />
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          <button
            onClick={handleSubmit}
            disabled={isLoading || !isFormValid || isOverLimit}
            className={`
              flex items-center gap-2 px-8 py-3 rounded-full font-semibold text-white shadow-lg transition-all
              ${
                isLoading || !isFormValid || isOverLimit
                  ? "bg-gray-400 cursor-not-allowed transform-none"
                  : "bg-linear-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 hover:shadow-blue-500/25 active:scale-95"
              }
            `}
          >
            {isLoading ? (
              <>
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Generating...
              </>
            ) : isOverLimit ? (
              <>
                <Sparkles size={18} className="text-gray-200" />
                현재 할당량이 초과되어 대기하여야 합니다.
              </>
            ) : (
              <>
                <Sparkles size={18} className={config.mode !== 'text-to-image' ? "animate-pulse" : ""} />
                Generate
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
});
