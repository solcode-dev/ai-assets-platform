import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { GenerationMode, AssetStatusType } from '@/types/image';

export type TaskStatus = 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';

/** 완료되거나 실패한 태스크를 로컬 스토리지에서 유지하는 시간 (24시간) */
export const TASK_GC_THRESHOLD = 24 * 60 * 60 * 1000;

/** 진행 중인 태스크의 강제 타임아웃 시간 (1시간) */
export const TASK_PENDING_TIMEOUT = 1 * 60 * 60 * 1000;

/** 네트워크 오류 시 최대 재시도 횟수 */
const MAX_RETRY_COUNT = 3;

export interface TaskState {
  id: string;
  mode: GenerationMode;
  status: TaskStatus;
  createdAt: number;
  updatedAt: number;     // 서버 기준 타임스탬프 (Freshness 체크용)
  retryCount: number;
  isRead: boolean;
  resultUrl?: string;    // 🆕 생성 완료된 이미지/비디오 URL
  error?: string;        // 🆕 실패 시 에러 메시지
}

/** 🆕 서버 응답용 인터페이스 (Backend AssetResponse와 매칭) */
interface ServerTaskResponse {
  job_id: string;
  status: TaskStatus;
  created_at: string;     // ISO 8601
  asset_type: 'IMAGE' | 'VIDEO';
  mode?: GenerationMode;
  updated_at: string;     // 🆕 추가
  result_url?: string;    // 🆕 추가
  error_message?: string; // 🆕 추가
}

export interface TaskStore {
  // Internal state
  _hasHydrated: boolean;
  setHasHydrated: (state: boolean) => void;
  _subscribeToStorageEvents: () => () => void;
  
  // Business state
  tasks: Record<string, TaskState>;
  lastSyncTime: number;
  selectedJobId: string | null; // 현재 상세보기 중인 에셋 ID
  
  // Actions
  addTask: (id: string, mode: GenerationMode, status?: TaskStatus) => void;
  updateTask: (id: string, updates: Partial<TaskState>) => void;
  removeTask: (id: string) => void;
  setSelectedJobId: (id: string | null) => void; // 상세보기 제어 액션
  
  // SSE 전용 액션: 특정 작업의 상태만 즉시 업데이트
  syncTaskFromEvent: (payload: {
    jobId: string;
    status: AssetStatusType;
    resultUrl?: string;
    error?: string;
    updatedAt?: string; // ISO 8601
  }) => void;
  
  // Notification Actions
  markAsRead: (id: string) => void;
  markAllAsRead: () => void;
  clearAllTasks: () => void;
  
  // Settings
  
  clearOldTasks: () => void;
  syncTasks: () => Promise<void>;
}

// Helper: 안전한 서버 시간 파싱
const parseServerTime = (isoString: string | undefined | null): number => {
  if (!isoString) return Date.now();
  const timestamp = new Date(isoString).getTime();
  if (isNaN(timestamp)) {
    console.warn(`Invalid date: ${isoString}, using current time`);
    return Date.now();
  }
  return timestamp;
};

/** 🆕 에셋 타입을 기반으로 생성 모드 추론 (백엔드에 mode 필드가 없을 때의 Fallback) */
const inferModeFromAssetType = (assetType: string): GenerationMode => {
  return assetType === 'IMAGE' ? 'text-to-image' : 'text-to-video';
};

export const useTaskStore = create<TaskStore>()(
  persist(
    (set, get) => ({
      // Internal state
      _hasHydrated: false,
      setHasHydrated: (state) => set({ _hasHydrated: state }),
      
      _subscribeToStorageEvents: () => {
        const handleStorageChange = (e: StorageEvent) => {
          if (e.key === 'task-storage' && e.newValue) {
            // ✅ Zustand API 재사용 (DRY)
            useTaskStore.persist.rehydrate();
          }
        };
        window.addEventListener('storage', handleStorageChange);
        return () => window.removeEventListener('storage', handleStorageChange);
      },
      
      // Business state
      tasks: {} as Record<string, TaskState>,
      lastSyncTime: Date.now(),
      selectedJobId: null as string | null,
      
      // Actions
      addTask: (id: string, mode: GenerationMode, status: TaskStatus = 'PENDING') => set((state: TaskStore) => ({
        tasks: {
          ...state.tasks,
          [id]: {
            id,
            mode,
            status,
            createdAt: Date.now(),
            updatedAt: Date.now(),
            retryCount: 0,
            isRead: true, // 생성 시점에는 본인이 만든 것이므로 '읽음' 처리
          }
        }
      })),
      
      updateTask: (id: string, updates: Partial<TaskState>) => set((state: TaskStore) => ({
        tasks: {
          ...state.tasks,
          [id]: { ...state.tasks[id], ...updates, updatedAt: Date.now() }
        }
      })),
      
      removeTask: (id: string) => set((state: TaskStore) => {
        const { [id]: _, ...rest } = state.tasks;
        return { tasks: rest };
      }),

      setSelectedJobId: (selectedJobId: string | null) => set({ selectedJobId }),

      syncTaskFromEvent: ({ jobId, status, resultUrl, error, updatedAt }: { jobId: string; status: AssetStatusType; resultUrl?: string; error?: string; updatedAt?: string }) => set((state: TaskStore) => {
        const existingTask = state.tasks[jobId];
        if (!existingTask) return state;

        const serverTime = parseServerTime(updatedAt);
        
        console.debug(`[HAWKEYE:SSE] Received update for ${jobId}: ${status}`, { error, resultUrl, updatedAt });

        // 1. 데이터 역행 방지: 기존 데이터가 더 최신이면 무시
        if (existingTask.updatedAt > serverTime) {
          console.warn(`[HAWKEYE:SSE] Outdated event ignored for ${jobId}. (Store: ${existingTask.updatedAt}, Event: ${serverTime})`);
          return state;
        }

        // 2. 불필요한 업데이트 방지: 상태가 같으면 무시 (단, 결과 URL이 새로 들어오면 예외)
        if (existingTask.status === status && existingTask.resultUrl === resultUrl && existingTask.error === error) {
          console.debug(`[HAWKEYE:SSE] No meaningful change for ${jobId}. Skipping update.`);
          return state;
        }

        console.info(`[HAWKEYE:STORE] Updating task ${jobId}: ${existingTask.status} -> ${status}`);

        // 상태 변화여부 확인
        const isNewNotification = 
          (status === 'COMPLETED' || status === 'FAILED') && 
          !['COMPLETED', 'FAILED'].includes(existingTask.status);

        // Toast 알림 로직 제거 (useGenerationJob에서 로컬 처리)

        return {
          tasks: {
            ...state.tasks,
            [jobId]: {
              ...existingTask,
              status,
              resultUrl: resultUrl || existingTask.resultUrl,
              error: (error !== undefined && error !== null) ? error : existingTask.error,
              isRead: isNewNotification ? false : existingTask.isRead,
              updatedAt: serverTime,
            },
          },
          // ✨ Auto-open Logic: 완료 시 무조건 모달 오픈
          selectedJobId: (isNewNotification && status === 'COMPLETED') 
            ? jobId 
            : state.selectedJobId
        };
      }),

      // Notification Actions
      markAsRead: (id: string) => set((state: TaskStore) => ({
        tasks: {
          ...state.tasks,
          [id]: { ...state.tasks[id], isRead: true }
        }
      })),

      markAllAsRead: () => set((state: TaskStore) => {
        const newTasks = { ...state.tasks };
        Object.keys(newTasks).forEach(id => {
          if (['COMPLETED', 'FAILED'].includes(newTasks[id].status)) {
            newTasks[id] = { ...newTasks[id], isRead: true };
          }
        });
        return { tasks: newTasks };
      }),

      clearAllTasks: () => set({ tasks: {} }),
      
      clearOldTasks: () => set((state: TaskStore) => {
        const now = Date.now();
        const newTasks = { ...state.tasks };
        let hasChanges = false;

        Object.keys(newTasks).forEach(id => {
          const task = newTasks[id];
          const isCompletedOld = (now - task.updatedAt > TASK_GC_THRESHOLD) && ['COMPLETED', 'FAILED'].includes(task.status);
          const isPendingTimeout = (now - task.createdAt > TASK_PENDING_TIMEOUT) && ['PENDING', 'PROCESSING'].includes(task.status);
          
          if (isCompletedOld) {
            delete newTasks[id];
            hasChanges = true;
          } else if (isPendingTimeout) {
            console.warn(`[HAWKEYE:STORE] Task ${id} timed out. Marking as FAILED.`);
            newTasks[id] = {
              ...task,
              status: 'FAILED',
              error: 'Task timed out (stuck locally for > 1h)',
              updatedAt: now,
              isRead: false
            };
            hasChanges = true;
          }
        });

        return hasChanges ? { tasks: newTasks } : state;
      }),
      
      syncTasks: async () => {
        const currentTasks = get().tasks;
        const now = Date.now();
        
        // ✅ 30분 이내이면서 PENDING/PROCESSING인 작업만 추출
        const pendingIds = Object.keys(currentTasks).filter(
          id => {
            const task = currentTasks[id];
            const isPending = ['PENDING', 'PROCESSING'].includes(task.status);
            const isNotTooOld = now - task.createdAt < TASK_GC_THRESHOLD;
            return isPending && isNotTooOld;
          }
        );
        
        console.log(`[HAWKEYE:STORE] syncTasks triggered. Pending candidates: ${pendingIds.length}`, pendingIds);
        
        if (pendingIds.length === 0) return;
        
        try {
          const response = await fetch('/api/assets/batch-status', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ task_ids: pendingIds })
          });
          
          if (!response.ok) throw new Error(`HTTP ${response.status}`);
          
          const { tasks: serverTasks }: { tasks: ServerTaskResponse[] } = await response.json();
          
          // 1. 알림 대상 미리 추출 (업데이트 전 상태)
          const oldTasks = get().tasks;
          const completedTasks = serverTasks.filter((task) => 
            task.status === 'COMPLETED' && 
            oldTasks[task.job_id]?.status !== 'COMPLETED'
          );
          
          // 2. 단일 배치 업데이트 (1번 리렌더링)
          set((state: TaskStore) => {
            const newTasks = { ...state.tasks };
            const returnedIds = new Set(serverTasks.map(t => t.job_id));
            
            // 2-1. 서버에 존재하는 작업 업데이트
            serverTasks.forEach((serverTask) => {
              const existing = newTasks[serverTask.job_id];
              const serverTime = parseServerTime(serverTask.updated_at);

              if (existing) {
                // 데이터 역행 방지
                // 단, 서버 상태가 COMPLETED/FAILED인 경우(최종 상태)에는 로컬 시간보다 과거라도 강제 업데이트 허용
                // (예: 로컬에서 재시도 등으로 시간이 갱신되었지만 실제로는 이미 완료된 경우)
                const isTerminalUpdate = ['COMPLETED', 'FAILED'].includes(serverTask.status);
                
                if (existing.updatedAt > serverTime && !isTerminalUpdate) {
                  console.warn(`[HAWKEYE:STORE] Skipping update for ${serverTask.job_id}. Local: ${existing.updatedAt} > Server: ${serverTime}`);
                  return;
                }

                const nextStatus = serverTask.status;
                const isNewNotification = 
                  ['PENDING', 'PROCESSING'].includes(existing.status) && 
                  ['COMPLETED', 'FAILED'].includes(nextStatus);

                newTasks[serverTask.job_id] = {
                  ...existing,
                  status: nextStatus as TaskStatus,
                  resultUrl: serverTask.result_url || existing.resultUrl,
                  error: serverTask.error_message, // 🆕 폴링 시 에러 메시지 동기화
                  updatedAt: serverTime,
                  retryCount: 0,
                  isRead: isNewNotification ? false : existing.isRead,
                };
              } else {
                // 서버 태스크 추가 (Data Integrity)
                newTasks[serverTask.job_id] = {
                  id: serverTask.job_id,
                  mode: serverTask.mode || inferModeFromAssetType(serverTask.asset_type),
                  status: serverTask.status as TaskStatus,
                  createdAt: parseServerTime(serverTask.created_at),
                  updatedAt: serverTime,
                  retryCount: 0,
                  isRead: !['COMPLETED', 'FAILED'].includes(serverTask.status),
                  resultUrl: serverTask.result_url,
                  error: serverTask.error_message, // 🆕 초기 로드 시 에러 메시지 동기화
                };
              }
            });

            // 2-2. 서버에서 사라진 작업 처리 (Zombie Tasks)
            // 요청했던 ID 중 응답에 없는 것은 DB에서 삭제된 것으로 간주 -> FAILED 처리
            pendingIds.forEach(pendingId => {
              if (!returnedIds.has(pendingId) && newTasks[pendingId]) {
                console.warn(`[HAWKEYE:STORE] Task ${pendingId} not found on server. Marking as FAILED.`);
                newTasks[pendingId] = {
                  ...newTasks[pendingId],
                  status: 'FAILED',
                  error: 'Job not found on server (possibly deleted)',
                  updatedAt: Date.now(),
                  isRead: false // 알림 표시
                };
              }
            });
            
            return { tasks: newTasks, lastSyncTime: Date.now() };
          });
          
          // 3. 완료 알림
          if (completedTasks.length > 0) {
            console.log(`🎉 ${completedTasks.length}개 작업 완료!`);
            // TODO: Phase 4에서 Toast 추가
          }
          
        } catch (error) {
          console.error('syncTasks failed:', error);
          
          // 4. 재시도 로직 (MAX 3회)
          set((state: TaskStore) => {
            const newTasks = { ...state.tasks };
            
            pendingIds.forEach(id => {
              if (newTasks[id]) {
                const newRetryCount = (newTasks[id].retryCount || 0) + 1;
                newTasks[id] = {
                  ...newTasks[id],
                  retryCount: newRetryCount,
                  status: newRetryCount >= MAX_RETRY_COUNT ? 'FAILED' : newTasks[id].status,
                };
              }
            });
            
            return { tasks: newTasks };
          });
        }
      }
    }),
    {
      name: 'task-storage',
      version: 1,
      storage: createJSONStorage(() => localStorage),
      onRehydrateStorage: () => (state) => {
        state?.setHasHydrated(true);
      }
    }
  )
);

// Custom Hook: Hydration 완료 여부 확인
export const useHasHydrated = () => {
  return useTaskStore((state) => state._hasHydrated);
};

// Helper Hook: 읽지 않은 완료/실패 알림 개수
export const useUnreadCount = () => {
  return useTaskStore((state) => 
    Object.values(state.tasks).filter(task => 
      ['COMPLETED', 'FAILED'].includes(task.status) && !task.isRead
    ).length
  );
};
