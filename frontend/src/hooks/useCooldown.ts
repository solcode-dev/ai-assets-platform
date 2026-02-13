import { useState, useEffect, useCallback } from 'react';

// 탭별 격리된 쿨다운을 위해 sessionStorage 키 사용
const COOLDOWN_KEY = 'generation_cooldown_end_time';

interface UseCooldownReturn {
  isCooldown: boolean;
  remainingTime: number;
  startCooldown: (seconds: number) => void;
  resetCooldown: () => void;
}

export function useCooldown(): UseCooldownReturn {
  const [remainingTime, setRemainingTime] = useState<number>(0);

  // 초기 로드 시 sessionStorage에서 쿨다운 상태 복원
  useEffect(() => {
    const checkCooldown = () => {
      const storedEndTime = sessionStorage.getItem(COOLDOWN_KEY);
      if (storedEndTime) {
        const endTime = parseInt(storedEndTime, 10);
        const now = Date.now();
        const diff = Math.ceil((endTime - now) / 1000);

        if (diff > 0) {
          setRemainingTime(diff);
        } else {
          // 시간이 지났으면 정리
          setRemainingTime(0);
          sessionStorage.removeItem(COOLDOWN_KEY);
        }
      }
    };

    checkCooldown();
    // 탭 격리이므로 storage 이벤트 리스너 제거
  }, []);

  // 타이머 로직
  useEffect(() => {
    if (remainingTime <= 0) return;

    const intervalId = setInterval(() => {
      setRemainingTime((prev) => {
        if (prev <= 1) {
          clearInterval(intervalId);
          sessionStorage.removeItem(COOLDOWN_KEY); // 종료 시 삭제
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(intervalId);
  }, [remainingTime]);

  const startCooldown = useCallback((seconds: number) => {
    const now = Date.now();
    const endTime = now + seconds * 1000;
    
    sessionStorage.setItem(COOLDOWN_KEY, endTime.toString());
    setRemainingTime(seconds);
  }, []);

  const resetCooldown = useCallback(() => {
    sessionStorage.removeItem(COOLDOWN_KEY);
    setRemainingTime(0);
  }, []);

  return {
    isCooldown: remainingTime > 0,
    remainingTime,
    startCooldown,
    resetCooldown
  };
}
