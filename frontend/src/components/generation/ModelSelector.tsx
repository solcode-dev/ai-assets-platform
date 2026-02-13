import React from 'react';
import { ChevronDown } from 'lucide-react';

// TODO: 실제 모델 목록은 상수 파일이나 API에서 가져오도록 확장 가능
export type ModelType = 
  | 'imagen-3.0-fast-generate-001'
  | 'veo-3.0-fast-generate-001';

interface ModelSelectorProps {
  currentModel: ModelType;
  onModelChange?: (model: ModelType) => void;
  disabled?: boolean;
}

export const ModelSelector = ({ 
  currentModel, 
  onModelChange, 
  disabled = false 
}: ModelSelectorProps) => {
  return (
    <div className="flex items-center gap-2">
      <span className="text-sm text-gray-500">Model:</span>
      <button 
        disabled={disabled || !onModelChange}
        className={`
          flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-mono border transition-all
          ${disabled 
            ? 'bg-gray-100 text-gray-400 border-gray-200 cursor-not-allowed' 
            : 'bg-white text-blue-600 border-blue-100 hover:border-blue-300 hover:bg-blue-50'
          }
        `}
      >
        <span>{currentModel}</span>
        {onModelChange && <ChevronDown size={14} className="opacity-50" />}
      </button>
    </div>
  );
};
