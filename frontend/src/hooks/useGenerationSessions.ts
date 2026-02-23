import { useState, useCallback } from 'react';
import { GenerationMode } from '@/types/image';

export interface SessionData {
  prompt: string;
  sourceImage: File | null;
}

const INITIAL_SESSIONS: Record<GenerationMode, SessionData> = {
  'text-to-image': { prompt: '', sourceImage: null },
  'text-to-video': { prompt: '', sourceImage: null },
  'image-to-video': { prompt: '', sourceImage: null },
};

/**
 * Generation 세션 상태를 관리하는 커스텀 훅
 * - 모드별 독립적인 프롬프트 및 이미지 데이터 보존
 * - 탭 전환 시 데이터 유실 방지
 * - 비즈니스 로직과 UI 관심사 분리
 */
export const useGenerationSessions = (initialPrompt: string = '') => {
  const [sessions, setSessions] = useState<Record<GenerationMode, SessionData>>(() => ({
    ...INITIAL_SESSIONS,
    'text-to-image': { ...INITIAL_SESSIONS['text-to-image'], prompt: initialPrompt }
  }));
  const [currentMode, setCurrentMode] = useState<GenerationMode>('text-to-image');

  /**
   * 설정 통합 업데이트 (제어 컴포넌트 패턴 지원)
   * 1. 모드 변경 시: 세션 데이터는 건드리지 않고 currentMode만 전환
   * 2. 데이터 변경 시: 현재 모드의 세션 데이터만 업데이트
   */
  const updateConfig = useCallback((newConfig: { mode: GenerationMode; prompt: string; sourceImage: File | null }) => {
    // 탭 전환 감지
    if (newConfig.mode !== currentMode) {
      setCurrentMode(newConfig.mode);
      return;
    }

    // 현재 모드의 데이터 업데이트 (입력 중)
    setSessions(prev => ({
      ...prev,
      [currentMode]: {
        prompt: newConfig.prompt,
        sourceImage: newConfig.sourceImage,
      },
    }));
  }, [currentMode]);

  /**
   * 생성 성공 시 현재 모드의 텍스트만 전용으로 초기화
   */
  const clearPrompt = useCallback(() => {
    setSessions(prev => ({
      ...prev,
      [currentMode]: { ...prev[currentMode], prompt: '' },
    }));
  }, [currentMode]);

  return {
    sessions,
    currentMode,
    updateConfig,
    clearPrompt,
  };
};
