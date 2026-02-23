import { useState, useEffect, useRef } from 'react';

interface UseFakeProgressProps {
  isLoading: boolean;
  expectedDuration?: number; // 예상 소요 시간 (ms)
}

/**
 * 지수 함수 기반의 가상 프로그레스 훅
 * - isLoading이 true일 때 0%에서 시작하여 99%까지 점진적 증가
 * - 초기에는 빠르게 증가하다가 후반부에는 천천히 증가 (체감 속도 최적화)
 * - isLoading이 false가 되면(완료) 즉시 100%로 도달
 */
export const useFakeProgress = ({ 
  isLoading, 
  expectedDuration = 6000 // 기본값 6초 (T2I 평균 고려)
}: UseFakeProgressProps) => {
  const [progress, setProgress] = useState(0);
  const startTimeRef = useRef<number | null>(null);
  const rafRef = useRef<number | null>(null);

  useEffect(() => {
    // 1. 로딩 시작
    if (isLoading) {
      // 시작 시점에만 초기화하도록 수정 (불필요한 re-render 방지)
      if (startTimeRef.current === null) {
        startTimeRef.current = Date.now();
        // setProgress(0) 제거: animate()에서 첫 프레임 계산 시 0에 수렴하거나,
        // 필요하다면 animate 내부에서 처리. Lint 에러 방지.
      }
      
      const animate = () => {
        if (!startTimeRef.current) return;
        
        const elapsedTime = Date.now() - startTimeRef.current;
        
        // 지수 함수: 1 - e^(-k * t)
        // k값은 expectedDuration에 맞춰 조정. 목표는 expectedDuration 시점에 약 80~90% 도달.
        // 예를 들어 3초일 때 90%라면: 0.9 = 1 - e^(-3k) -> e^(-3k) = 0.1 -> -3k = ln(0.1) ~ -2.3 -> k ~ 0.76
        // 좀 더 부드럽게: k = 2 / (expectedDuration / 1000)
        const timeInSeconds = elapsedTime / 1000;
        const k = 2.5 / (expectedDuration / 1000); 
        
        // 99%까지만 수렴하도록 제한
        // 수식: progress = 99 * (1 - exp(-k * t))
        const rawProgress = 99 * (1 - Math.exp(-k * timeInSeconds));
        
        setProgress(Math.min(rawProgress, 99));
        
        rafRef.current = requestAnimationFrame(animate);
      };

      rafRef.current = requestAnimationFrame(animate);
    } 
    // 2. 로딩 완료 (isLoading: true -> false)
    else {
      if (startTimeRef.current !== null) { // 이전에 로딩 중이었다면
        setTimeout(() => setProgress(100), 0);
      } else {
        setTimeout(() => setProgress(0), 0); // 초기 상태
      }
      
      if (rafRef.current) {
        cancelAnimationFrame(rafRef.current);
        rafRef.current = null;
      }
      startTimeRef.current = null;
    }

    return () => {
      if (rafRef.current) {
        cancelAnimationFrame(rafRef.current);
      }
    };
  }, [isLoading, expectedDuration]);

  return progress;
};
