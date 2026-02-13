import { create } from 'zustand';

interface SystemState {
  isHealthy: boolean;
  setSystemStatus: (status: boolean) => void;
}

export const useSystemStore = create<SystemState>((set) => ({
  isHealthy: true, // 초기 상태는 정상으로 가정
  setSystemStatus: (status) => set({ isHealthy: status }),
}));
