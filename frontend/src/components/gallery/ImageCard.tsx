'use client';

import { useState } from 'react';
import Image from 'next/image';

interface ImageCardProps {
  src: string;
  alt: string;
  aspectRatio: string;  // "4/5" 형태
  blurDataURL?: string;
  priority?: boolean;
  className?: string;
  overlay?: React.ReactNode;
  onClick?: () => void;
  similarityScore?: number;
}

const FALLBACK_IMAGE = '/placeholder.svg';

export function ImageCard({ 
  src, 
  alt, 
  aspectRatio,
  blurDataURL,
  priority = false, 
  className,
  overlay,
  onClick,
  similarityScore
}: ImageCardProps) {
  const [hasError, setHasError] = useState(false);
  const displaySrc = hasError || !src ? FALLBACK_IMAGE : src;

  return (
    <article 
      onClick={onClick}
      className={`relative rounded-xl overflow-hidden group cursor-pointer ${className ?? ''}`}
      style={{ aspectRatio }}
    >
      <Image
        src={displaySrc}
        alt={alt}
        fill
        sizes="(max-width: 768px) 50vw, (max-width: 1200px) 33vw, 20vw"
        onError={(e) => {
          console.error(`[ImageCard] FAILED to load: "${src}" (displaySrc: "${displaySrc}")`, e);
          setHasError(true);
        }}
        className="object-cover transition-transform duration-300 group-hover:scale-105 will-change-transform"
        priority={priority}
        placeholder={blurDataURL ? 'blur' : 'empty'}
        blurDataURL={blurDataURL}
      />
      
      {/* 유사도 점수 배지 (검색 결과 시 표시) */}
      {(() => {
        // console.log(`[ImageCard] id: ${src}, score: ${similarityScore}`);
        return null;
      })()}
      {similarityScore !== undefined && (similarityScore >= 0.1 || similarityScore > 0.015) && (
        <div className="absolute top-2 left-2 z-10 px-2 py-1 bg-black/60 backdrop-blur-md rounded-lg text-[10px] font-bold text-white border border-white/20 shadow-lg animate-in fade-in zoom-in duration-300">
          {similarityScore < 0.1 
            ? (similarityScore > 0.03 ? "최적 일치" : "높은 연관성") 
            : `${Math.round(similarityScore * 100)}% 일치`}
        </div>
      )} 

      {overlay}
    </article>
  );
}
