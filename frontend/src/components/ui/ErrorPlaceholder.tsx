import { AlertTriangle, RefreshCw } from 'lucide-react';
import { Button } from './Button';

interface ErrorPlaceholderProps {
  message?: string;
  onRetry?: () => void;
}

export function ErrorPlaceholder({
  message = '이미지를 불러올 수 없습니다',
  onRetry
}: ErrorPlaceholderProps) {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-gray-500">
      <AlertTriangle size={48} className="text-gray-400 mb-4" />
      <p className="text-lg font-medium">{message}</p>
      <p className="text-sm mb-4">네트워크 연결을 확인해주세요</p>
      {onRetry && (
        <Button onClick={onRetry} variant="secondary">
          <RefreshCw size={16} className="mr-2" />
          다시 시도
        </Button>
      )}
    </div>
  );
}
