'use client';

import { useState, useEffect } from 'react';
import { Download, Calendar, Image as ImageIcon, Sparkles, Video } from 'lucide-react';
import { useAssetDownload } from '@/hooks/useAssetDownload';

import { AssetType, ASSET_TYPE } from '@/types/image';

interface AssetMetadataProps {
  assetId: string;
  src?: string;
  prompt: string;
  model: string;
  width: number;
  height: number;
  createdAt: string;
  assetType: AssetType;
}

export function AssetMetadata({
  assetId,
  src,
  prompt,
  model,
  width,
  height,
  createdAt,
  assetType,
}: AssetMetadataProps) {
  const { isDownloading, download } = useAssetDownload({ assetId, assetType });
  const [actualDimensions, setActualDimensions] = useState<{ width: number; height: number } | null>(null);

  useEffect(() => {
    if (!src) {
      return;
    }

    if (assetType === ASSET_TYPE.VIDEO) {
      const video = document.createElement('video');
      video.onloadedmetadata = () => {
        setActualDimensions({ width: video.videoWidth, height: video.videoHeight });
      };
      video.src = src;
    } else {
      const img = new window.Image();
      img.onload = () => {
        setActualDimensions({ width: img.naturalWidth, height: img.naturalHeight });
      };
      img.src = src;
    }

    return () => {
      setActualDimensions(null);
    };
  }, [src, assetType]);

  const displayWidth = actualDimensions?.width ?? width;
  const displayHeight = actualDimensions?.height ?? height;

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('ko-KR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="pb-4 border-b border-gray-200 dark:border-gray-700">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
          Details
        </h2>
      </div>

      {/* Metadata Content */}
      <div className="flex-1 py-6 space-y-6 overflow-y-auto">
        {/* Prompt */}
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-sm font-medium text-gray-500 dark:text-gray-400">
            <Sparkles size={16} />
            <span>Prompt</span>
          </div>
          <p className="text-sm text-gray-900 dark:text-white leading-relaxed">
            {prompt}
          </p>
        </div>

        {/* Model */}
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-sm font-medium text-gray-500 dark:text-gray-400">
            <ImageIcon size={16} />
            <span>Model</span>
          </div>
          <p className="text-sm text-gray-900 dark:text-white">{model}</p>
        </div>

        {/* Asset Type */}
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-sm font-medium text-gray-500 dark:text-gray-400">
            {assetType === ASSET_TYPE.VIDEO ? <Video size={16} /> : <ImageIcon size={16} />}
            <span>Type</span>
          </div>
          <div className="flex">
            <span className={`
              inline-flex items-center px-2.5 py-0.5 rounded-full text-s font-medium
              ${assetType === ASSET_TYPE.VIDEO 
                ? 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300' 
                : 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300'
              }
            `}>
              {assetType === ASSET_TYPE.VIDEO ? 'Video' : 'Image'}
            </span>
          </div>
        </div>

        {/* Dimensions */}
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-sm font-medium text-gray-500 dark:text-gray-400">
            {assetType === ASSET_TYPE.VIDEO ? <Video size={16} /> : <ImageIcon size={16} />}
            <span>Dimensions</span>
          </div>
          <p className="text-sm text-gray-900 dark:text-white">
            {displayWidth} × {displayHeight} px
          </p>
        </div>

        {/* Created Date */}
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-sm font-medium text-gray-500 dark:text-gray-400">
            <Calendar size={16} />
            <span>Created</span>
          </div>
          <p className="text-sm text-gray-900 dark:text-white">
            {formatDate(createdAt)}
          </p>
        </div>
      </div>

      {/* Download Button */}
      <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
        <button
          onClick={download}
          disabled={isDownloading}
          aria-busy={isDownloading}
          aria-label={isDownloading ? '다운로드 중입니다' : '이미지 다운로드'}
          className={`
            w-full flex items-center justify-center gap-2 px-4 py-3 
            rounded-lg font-medium transition-all
            ${
              isDownloading
                ? 'bg-gray-100 dark:bg-gray-800 text-gray-400 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700 text-white shadow-sm hover:shadow-md'
            }
          `}
        >
          {isDownloading ? (
            <>
              <svg
                className="animate-spin h-5 w-5"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
              <span aria-live="polite">다운로드 중...</span>
            </>
          ) : (
            <>
              <Download size={20} aria-hidden="true" />
              <span>다운로드</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
}
