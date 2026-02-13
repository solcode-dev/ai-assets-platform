'use client';

import { useEffect, useCallback } from 'react';
import { useQuotaStore } from '@/stores/useQuotaStore';

const POLL_INTERVAL = 1000; // 3초마다 할당량 체크

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function QuotaManager() {
  const setStats = useQuotaStore((state) => state.setStats);
  const setError = useQuotaStore((state) => state.setError);

  const checkQuota = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/system/stats`);
      if (!response.ok) throw new Error('Failed to fetch stats');
      
      const json = await response.json();
      if (json.success && json.data) {
        setStats(json.data);
      }
    } catch (err) {
      console.error('[QuotaManager] Quota check failed:', err);
      setError();
    }
  }, [setStats, setError]);

  useEffect(() => {
    // 즉시 실행
    checkQuota();

    // 주기적 호출
    const timer = setInterval(checkQuota, POLL_INTERVAL);
    return () => clearInterval(timer);
  }, [checkQuota]);

  // UI를 렌더링하지 않는 데이터 관리용 컴포넌트
  return null;
}
