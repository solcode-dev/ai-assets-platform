'use client';

import React, { createContext, useContext, useEffect, useRef } from 'react';
import { useTaskStore } from '@/stores/useTaskStore';
import { AssetStatusType } from '@/types/image';

const SSEContext = createContext<null>(null);

const SSE_URL = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/assets/stream`;

export const SSEProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const syncTaskFromEvent = useTaskStore((state) => state.syncTaskFromEvent);
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    let reconnectTimeout: NodeJS.Timeout;

    const connect = () => {
      console.log('[SSE] Connecting to:', SSE_URL);
      const es = new EventSource(SSE_URL);
      eventSourceRef.current = es;

      es.onopen = () => {
        console.log('[SSE] Connection opened');
      };

      es.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('[SSE] Received event:', data);
          
          if (data.job_id && data.status) {
            // 상세 데이터 업데이트
            syncTaskFromEvent({
              jobId: data.job_id, 
              status: data.status.toUpperCase() as AssetStatusType,
              resultUrl: data.result_url,
              error: data.error,
              updatedAt: data.updated_at
            });
          }
        } catch (err) {
          console.error('[SSE] Failed to parse event data:', err);
        }
      };

      es.onerror = (err) => {
        console.error('[SSE] Connection error:', err);
        es.close();
        
        // 5초 후 재연결 시도
        reconnectTimeout = setTimeout(() => {
          console.log('[SSE] Attempting to reconnect...');
          connect();
        }, 5000);
      };
    };

    connect();

    return () => {
      if (eventSourceRef.current) {
        console.log('[SSE] Closing connection');
        eventSourceRef.current.close();
      }
      clearTimeout(reconnectTimeout);
    };
  }, [syncTaskFromEvent]);

  return (
    <SSEContext.Provider value={null}>
      {children}
    </SSEContext.Provider>
  );
};

export const useSSE = () => useContext(SSEContext);
