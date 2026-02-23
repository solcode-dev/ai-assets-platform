import React, { useState } from 'react';
import { Eraser } from 'lucide-react';

interface TextPromptInputProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  disabled?: boolean;
  maxLength?: number;
}

export const TextPromptInput = ({
  value,
  onChange,
  placeholder = "Describe what you want to see...",
  disabled = false,
  maxLength = 1000
}: TextPromptInputProps) => {
  const [isShaking, setIsShaking] = useState(false);

  const handleClear = () => {
    if (disabled || !value) return;
    
    // 1. 흔들림 효과 시작
    setIsShaking(true);
    
    // 2. 실제 데이터 초기화
    onChange('');
    
    // 3. 애니메이션 종료 (0.4s 후)
    setTimeout(() => setIsShaking(false), 400);
  };

  return (
    <div className="relative w-full group">
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        disabled={disabled}
        maxLength={maxLength}
        className="w-full h-32 px-4 py-3 bg-white border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none resize-none transition-all text-gray-800 placeholder-gray-400 disabled:bg-gray-50 disabled:text-gray-400 pr-10"
      />
      
      {/* Eraser Button */}
      {value && !disabled && (
        <button
          onClick={handleClear}
          title="Clear prompt"
          disabled={disabled}
          className={`
            absolute top-3 right-3 p-1.5 rounded-lg transition-all duration-200
            bg-gray-50 text-gray-400 hover:text-blue-500 hover:bg-blue-50 
            group-hover:opacity-100 opacity-0 md:opacity-100
            ${isShaking ? 'animate-shake text-blue-600 bg-blue-100 scale-110' : 'active:scale-95'}
          `}
        >
          <Eraser size={16} className={`transition-transform ${!isShaking && 'hover:-rotate-12'}`} />
        </button>
      )}

      <div className="absolute bottom-3 right-3 text-xs text-gray-400 pointer-events-none bg-white/80 px-1 rounded">
        {value.length} / {maxLength}
      </div>
    </div>
  );
};
