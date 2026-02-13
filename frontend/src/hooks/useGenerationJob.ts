import { useState, useCallback, useEffect, useRef } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { GenerateRequest, GenerationJob, generateAsset } from '@/services/generation';
import { useTaskStore, TaskStore, TaskStatus } from '@/stores/useTaskStore';

interface UseGenerationJobReturn {
  startJob: (request: GenerateRequest) => Promise<{ job_id: string }>;
  jobStatus: GenerationJob['status'] | 'idle';
  currentJob: GenerationJob | null;
  error: string | null;
  reset: () => void;
  isStarting: boolean;
}

const KRAFTON_ACTIVE_JOB_ID = 'krafton_active_job_id';

export const useGenerationJob = (): UseGenerationJobReturn => {
  const queryClient = useQueryClient();
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);
  
  const syncTasks = useTaskStore(state => state.syncTasks);
  const markAsRead = useTaskStore(state => state.markAsRead);
  const _hasHydrated = useTaskStore(state => state._hasHydrated);
  
  const isRecoveredRef = useRef(false);

  // 1. Session recovery (only for non-terminal tasks)
  useEffect(() => {
    if (_hasHydrated && !currentJobId && !isRecoveredRef.current) {
      const savedJobId = sessionStorage.getItem(KRAFTON_ACTIVE_JOB_ID);
      const currentTasks = useTaskStore.getState().tasks;
      const targetTask = savedJobId ? currentTasks[savedJobId] : null;
      
      if (targetTask && !['COMPLETED', 'FAILED'].includes(targetTask.status)) {
        console.log('[useGenerationJob] Recovering active job:', savedJobId);
        // Avoid cascading renders with a timeout
        setTimeout(() => setCurrentJobId(savedJobId), 0);
      }
      isRecoveredRef.current = true;
    }
  }, [_hasHydrated, currentJobId]);

  // Stable task lookup
  const tasks = useTaskStore(state => state.tasks);
  const task = currentJobId ? tasks[currentJobId] : null;

  const mutation = useMutation({
    mutationFn: (req: GenerateRequest) => generateAsset(req),
    onSuccess: (data, variables) => {
      const jobId = data.job_id;
      setCurrentJobId(jobId);
      sessionStorage.setItem(KRAFTON_ACTIVE_JOB_ID, jobId);
      
      const status = (data.status?.toUpperCase() || 'PENDING') as TaskStatus;
      useTaskStore.getState().addTask(jobId, variables.mode, status);
      setTimeout(() => syncTasks(), 500); 
    },
    onError: (error) => {
      console.error('[useGenerationJob] Start error:', error);
    }
  });

  const jobStatus: GenerationJob['status'] | 'idle' = (() => {
    if (mutation.isPending) return 'pending';
    if (!task) return 'idle';
    switch (task.status) {
      case 'COMPLETED': return 'completed';
      case 'FAILED': return 'failed';
      case 'PROCESSING': return 'processing';
      default: return 'pending';
    }
  })();

  const reset = useCallback(() => {
    setCurrentJobId(null);
    mutation.reset();
    sessionStorage.removeItem(KRAFTON_ACTIVE_JOB_ID);
  }, [mutation]);

  const startJob = useCallback(async (request: GenerateRequest) => {
    setCurrentJobId(null);
    mutation.reset();
    return await mutation.mutateAsync(request);
  }, [mutation]);

  const error = mutation.error ? (mutation.error as Error).message : (task?.error || null);

  const currentJob: GenerationJob | null = task ? {
    job_id: task.id,
    status: jobStatus as GenerationJob['status'],
    result_url: task.resultUrl,
    error: task.error,
    created_at: new Date(task.createdAt).toISOString()
  } : null;

  // 4. Notifications and side effects
  // Use status/isRead specifically to keep the dependency array stable and meaningful
  const taskStatus = task?.status;
  const taskIsRead = task?.isRead;
  const taskError = task?.error;

  useEffect(() => {
    if (!currentJobId || !taskStatus) return;

    if (taskStatus === 'COMPLETED' && !taskIsRead) {
      toast.success('작업이 완료되었습니다!');
      markAsRead(currentJobId);
      queryClient.invalidateQueries({ queryKey: ['assets'] });
      // Keep it visible as per user request. No auto-reset.
    } 
    else if (taskStatus === 'FAILED' && !taskIsRead) {
      toast.error('작업이 실패했습니다.', {
        description: taskError || '알 수 없는 오류가 발생했습니다.'
      });
      markAsRead(currentJobId);
    }
  }, [taskStatus, taskIsRead, taskError, currentJobId, markAsRead, queryClient]);

  return {
    startJob,
    jobStatus,
    currentJob,
    error,
    reset,
    isStarting: mutation.isPending
  };
};
