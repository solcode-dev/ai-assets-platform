'use client';

import { useEffect } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/Button';

interface ErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function Error({ error, reset }: ErrorProps) {
  useEffect(() => {
    console.error('Page error:', error);
  }, [error]);

  return (
    <div className="flex flex-col items-center justify-center min-h-[50vh] text-gray-500">
      <AlertTriangle size={48} className="text-red-400 mb-4" />
      <h2 className="text-xl font-semibold mb-2">문제가 발생했습니다</h2>
      <p className="text-sm text-gray-400 mb-4">
        페이지를 표시하는 중 오류가 발생했습니다
      </p>
      <Button onClick={reset} variant="secondary">
        <RefreshCw size={16} className="mr-2" />
        다시 시도
      </Button>
    </div>
  );
}
