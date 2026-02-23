'use client';

import { useEffect, useRef } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useTaskStore, useHasHydrated, TASK_GC_THRESHOLD } from '@/stores/useTaskStore';

/**
 * TaskManager 컴포넌트
 * 
 * 역할:
 * 1. 초기 하이드레이션 완료 후 서버와 작업 상태 동기화 (Catch-up sync)
 * 2. 탭 포커스 시 즉시 동기화 (사용자가 돌아왔을 때 최신 상태 보장)
 * 3. 다른 탭에서의 변경 사항 구독 (Storage event)
 * 4. 진행 중인 작업이 있을 경우 30초마다 백업 폴링 (SSE 연결 끊김 대비)
 * 5. 주기적인 오래된 작업 정리 (GC)
 */
export function TaskManager() {
  const hasHydrated = useHasHydrated();
  const { syncTasks, clearOldTasks, _subscribeToStorageEvents } = useTaskStore();
  
  // tasks 전체를 구독하는 대신, 진행 중인 작업의 개수만 구독하여 불필요한 Effect 실행 방지
  const activeTasksCount = useTaskStore(state => 
    Object.values(state.tasks).filter(task => {
      const isPending = ['PENDING', 'PROCESSING'].includes(task.status);
      const isNotTooOld = Date.now() - task.createdAt < TASK_GC_THRESHOLD; // 30분 임계값
      return isPending && isNotTooOld;
    }).length
  );
  
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // 1. 초기 로드 및 이벤트 리스너 등록
  useEffect(() => {
    if (!hasHydrated) return;
    
    // 초기 동기화 및 정리
    clearOldTasks();
    syncTasks();
    
    // 멀티 탭 동기화 구독
    const unsubscribe = _subscribeToStorageEvents();
    
    // 윈도우 포커스 이벤트 (탭 전환 시 즉시 동기화)
    const handleFocus = () => {
      console.log('Tab focused, syncing tasks...');
      syncTasks();
    };
    window.addEventListener('focus', handleFocus);
    
    // 주기적인 GC (1분마다)
    const gcInterval = setInterval(clearOldTasks, 60000);
    
    return () => {
      unsubscribe();
      window.removeEventListener('focus', handleFocus);
      clearInterval(gcInterval);
    };
  }, [hasHydrated, syncTasks, clearOldTasks, _subscribeToStorageEvents]);

  // 2. 백업 폴링 로직: PENDING 또는 PROCESSING 상태의 작업이 있을 때만 동작
  useEffect(() => {
    if (!hasHydrated) return;

    if (activeTasksCount > 0) {
      if (!pollIntervalRef.current) {
        console.log(`Starting backup polling for ${activeTasksCount} active tasks...`);
        pollIntervalRef.current = setInterval(() => {
          console.log('Running 30s backup poll...');
          syncTasks();
        }, 30000);
      }
    } else {
      if (pollIntervalRef.current) {
        console.log('No active tasks, stopping backup polling.');
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }
    }

    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }
    };
  }, [hasHydrated, activeTasksCount, syncTasks]);

  // 3. 전역 갤러리 갱신 감지 (Observer)
  // useTaskStore의 상태 변화를 감지하여 COMPLETED 작업 발생 시 갤러리 갱신
  const tasks = useTaskStore(state => state.tasks);
  const prevTasksRef = useRef(tasks);
  const queryClient = useQueryClient();

  useEffect(() => {
    if (!hasHydrated) return;

    const prevTasks = prevTasksRef.current;
    const currentTasks = tasks;
    
    // 변경사항 감지
    const hasNewCompletion = Object.keys(currentTasks).some(id => {
      const prev = prevTasks[id];
      const curr = currentTasks[id];
      
      // 이전에는 없었거나 완료되지 않았는데 -> 지금 완료된 경우
      return curr.status === 'COMPLETED' && (!prev || prev.status !== 'COMPLETED');
    });

    if (hasNewCompletion) {
      console.log('[TaskManager] Global completion detected. Refreshing gallery...');
      queryClient.invalidateQueries({ queryKey: ['assets'] });
    }

    prevTasksRef.current = currentTasks;
  }, [tasks, hasHydrated, queryClient]);

  // UI를 렌더링하지 않는 로직 전용 컴포넌트
  return null;
}
