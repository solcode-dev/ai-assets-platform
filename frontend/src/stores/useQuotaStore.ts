import { create } from 'zustand';

export interface QuotaStats {
  active_requests: number;
  completed_requests: number;
  limit_requests: number;
}

interface QuotaState {
  stats: QuotaStats | null;
  isOverLimit: boolean;
  setStats: (stats: QuotaStats) => void;
  setError: () => void;
}

export const useQuotaStore = create<QuotaState>((set) => ({
  stats: null,
  isOverLimit: false,
  setStats: (stats) => set({ 
    stats, 
    isOverLimit: stats.active_requests >= stats.limit_requests 
  }),
  setError: () => set({ isOverLimit: false }), // 에러 시에는 버튼을 막지 않음
}));
