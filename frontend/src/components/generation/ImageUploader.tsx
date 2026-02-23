'use client';

import React, { useRef, useState, useEffect } from 'react';
import { Upload, X, AlertCircle } from 'lucide-react';
import Image from 'next/image';

interface ImageUploaderProps {
  selectedFile: File | null;
  onFileSelect: (file: File | null) => void;
  accept?: string;
  disabled?: boolean;
  maxSizeMB?: number; // 최대 파일 크기 (MB)
}

export const ImageUploader = ({
  selectedFile,
  onFileSelect,
  accept = "image/*",
  disabled = false,
  maxSizeMB = 10
}: ImageUploaderProps) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 컴포넌트 언마운트 시 메모리 정리
  useEffect(() => {
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [previewUrl]);

  const validateAndSetFile = (file: File) => {
    setError(null);

    // 1. 파일 크기 체크
    if (file.size > maxSizeMB * 1024 * 1024) {
      setError(`File size exceeds ${maxSizeMB}MB limit.`);
      return;
    }

    // 2. 파일 타입 체크 (간단한 검증)
    if (!file.type.startsWith('image/')) {
      setError('Only image files are allowed.');
      return;
    }

    // 3. 기존 URL 해제 (메모리 누수 방지)
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }

    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
    onFileSelect(file);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      validateAndSetFile(file);
    }
  };

  const handleClear = (e?: React.MouseEvent) => {
    e?.stopPropagation(); // 부모 클릭 전파 방지
    onFileSelect(null);
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
      setPreviewUrl(null);
    }
    setError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // Drag & Drop Handlers
  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!disabled) setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault(); // 필수: 이걸 해야 drop 이벤트가 발생함
    e.stopPropagation();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    if (disabled) return;

    const file = e.dataTransfer.files?.[0];
    if (file) {
      validateAndSetFile(file);
    }
  };

  const handleClick = () => {
    if (!disabled && !selectedFile) {
      fileInputRef.current?.click();
    }
  };

  return (
    <div className="w-full space-y-2">
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        accept={accept}
        className="hidden"
        disabled={disabled}
      />
      
      {selectedFile && previewUrl ? (
        <div className="relative w-full h-40 rounded-xl overflow-hidden border border-gray-200 group bg-gray-50">
          <Image 
            src={previewUrl} 
            alt="Selected source" 
            fill
            className="object-contain" // 이미지가 잘리지 않도록 contain으로 변경
          />
          <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
            <button
              onClick={handleClear}
              className="p-2 bg-white/20 hover:bg-white/40 rounded-full text-white transition-colors backdrop-blur-sm"
              title="Remove image"
            >
              <X size={20} />
            </button>
          </div>
        </div>
      ) : (
        <div
          onClick={handleClick}
          onDragEnter={handleDragEnter}
          onDragLeave={handleDragLeave}
          onDragOver={handleDragOver}
          onDrop={handleDrop}
          className={`
            relative w-full h-40 border-2 border-dashed rounded-xl flex flex-col items-center justify-center gap-3 transition-all duration-200
            ${error ? 'border-red-300 bg-red-50' : ''}
            ${!error && isDragging 
              ? 'border-blue-500 bg-blue-50 scale-[0.99] ring-4 ring-blue-100' 
              : !error && !disabled 
                ? 'border-gray-200 hover:border-blue-400 hover:bg-blue-50/50 cursor-pointer' 
                : ''
            }
            ${disabled ? 'border-gray-100 bg-gray-50 cursor-not-allowed opacity-60' : ''}
          `}
        >
          {error ? (
            <div className="text-center px-4 animate-in fade-in zoom-in duration-200">
              <div className="inline-flex p-2 rounded-full bg-red-100 text-red-500 mb-2">
                <AlertCircle size={20} />
              </div>
              <p className="text-sm font-medium text-red-600">{error}</p>
              <button 
                onClick={(e) => {
                  e.stopPropagation();
                  setError(null);
                }}
                className="mt-2 text-xs text-red-500 hover:text-red-700 underline"
              >
                Try again
              </button>
            </div>
          ) : (
            <>
              <div className={`
                p-3 rounded-full transition-colors
                ${isDragging ? 'bg-blue-100 text-blue-600' : 'bg-gray-50 text-gray-400'}
              `}>
                <Upload size={24} className={isDragging ? 'animate-bounce' : ''} />
              </div>
              <div className="text-center">
                <p className={`text-sm font-medium ${isDragging ? 'text-blue-600' : 'text-gray-600'}`}>
                  {isDragging ? 'Drop image here' : 'Click or drop image'}
                </p>
                <p className="text-xs text-gray-400 mt-1">
                  JPG, PNG up to {maxSizeMB}MB
                </p>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
};
