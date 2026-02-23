'use client';

import { useRef, useEffect } from 'react';

interface VideoCardProps {
  src: string;
  className?: string;
  aspectRatio: string;
  overlay?: React.ReactNode;
  onClick?: () => void;
  similarityScore?: number;
}

export function VideoCard({
  src,
  className,
  aspectRatio,
  overlay,
  onClick,
  similarityScore,
}: VideoCardProps) {
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    // 확실한 자동 재생 보장
    if (videoRef.current) {
      videoRef.current.play().catch(error => {
        // 자동 재생 정책에 의해 막힐 경우 처리 (보통 muted면 됨)
        console.warn('Video autoplay failed:', error);
      });
    }
  }, []);

  return (
    <article
      onClick={onClick}
      className={`relative rounded-xl overflow-hidden group cursor-pointer bg-black ${className ?? ''}`}
      style={{ aspectRatio }}
    >
      {src ? (
        <video
          ref={videoRef}
          src={src}
          className="object-cover w-full h-full transition-transform duration-300 group-hover:scale-105 will-change-transform"
          autoPlay
          loop
          muted
          playsInline
        />
      ) : (
        <div className="w-full h-full bg-gray-800 flex items-center justify-center text-gray-500 text-xs">
          Loading video...
        </div>
      )}
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
