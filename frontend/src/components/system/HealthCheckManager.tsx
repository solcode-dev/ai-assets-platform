'use client';

import { useEffect, useRef } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { useSystemStore } from '@/stores/useSystemStore';

export function HealthCheckManager() {
  const router = useRouter();
  const pathname = usePathname();
  const setSystemStatus = useSystemStore((state) => state.setSystemStatus);
  
  // 백오프 상태 관리 (Ref로 관리하여 리렌더링 방지)
  const retryCount = useRef(0);
  const timeoutId = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 3000); // 3초 타임아웃

        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/health`, {
          signal: controller.signal,
          cache: 'no-store', // 캐시 방지
        });
        
        clearTimeout(timeoutId);

        if (res.ok) {
          // 성공 시
          setSystemStatus(true);
          retryCount.current = 0; // 재시도 횟수 초기화
          
          // 정상 주기(5초)로 다음 체크 예약
          scheduleNextCheck(5000);
        } else {
          throw new Error('Health check failed');
        }
      } catch (error) {
        // 실패 시
        console.warn('System health check failed:', error);
        handleFailure();
      }
    };

    const handleFailure = () => {
      setSystemStatus(false);

      // 현재 페이지가 홈이 아니면 홈으로 리다이렉트
      if (pathname !== '/home') {
        router.push('/home');
      }

      // 지수 백오프 계산 (기본 5초 * 2^재시도횟수, 최대 60초)
      const delay = Math.min(5000 * Math.pow(2, retryCount.current), 60000);
      retryCount.current += 1; // 재시도 횟수 증가

      console.log(`Retrying health check in ${delay}ms...`);
      scheduleNextCheck(delay);
    };

    const scheduleNextCheck = (delay: number) => {
      if (timeoutId.current) clearTimeout(timeoutId.current);
      timeoutId.current = setTimeout(checkHealth, delay);
    };

    // 초기 실행
    checkHealth();

    return () => {
      if (timeoutId.current) clearTimeout(timeoutId.current);
    };
  }, [pathname, router, setSystemStatus]);

  return null; // UI 없음
}
