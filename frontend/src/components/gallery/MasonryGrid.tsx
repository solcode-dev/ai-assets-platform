"use client";

import { useEffect, useRef, useState, useMemo, useCallback } from "react";
import { GalleryImageSummary, ASSET_TYPE } from "@/types/image";
import { ImageCard } from "./ImageCard";
import { VideoCard } from "./VideoCard";
import { GalleryImageOverlay } from "./GalleryImageOverlay";
import { ImageDetailModal } from "./ImageDetailModal";
import { GlowingEffect } from "@/components/ui/glowing-effect";

interface MasonryGridProps {
  images: GalleryImageSummary[];
  isLoading?: boolean;
  onEndReached?: () => void;
}

const SKELETON_RATIOS = [
  "4/5",
  "1/1",
  "3/4",
  "16/9",
  "3/4",
  "4/5",
  "1/1",
  "16/9",
  "4/5",
  "3/4",
  "1/1",
  "4/5",
];
const COLUMN_WIDTH = 240;
const GAP = 12;

// 각 이미지의 절대 위치 계산 (Pinterest 스타일)
interface PositionedImage {
  image: GalleryImageSummary;
  left: number;
  top: number;
  width: number;
  height: number;
  originalIndex: number;
}

function calculateMasonryPositions(
  images: GalleryImageSummary[],
  containerWidth: number,
  columnWidth: number,
  gap: number,
): { positions: PositionedImage[]; totalHeight: number } {
  if (containerWidth <= 0 || images.length === 0) {
    return { positions: [], totalHeight: 0 };
  }

  // 열 개수 계산
  const columnCount = Math.max(
    1,
    Math.floor((containerWidth + gap) / (columnWidth + gap)),
  );
  const actualColumnWidth =
    (containerWidth - gap * (columnCount - 1)) / columnCount;

  // 각 열의 현재 높이 추적
  const columnHeights = new Array(columnCount).fill(0);
  const positions: PositionedImage[] = [];

  images.forEach((image, index) => {
    // 가장 짧은 열 찾기
    const minHeight = Math.min(...columnHeights);
    const columnIndex = columnHeights.indexOf(minHeight);

    // 이미지 높이 계산 (비율 유지)
    const imageHeight = Math.round(
      actualColumnWidth * (image.height / image.width),
    );

    // 위치 계산
    const left = columnIndex * (actualColumnWidth + gap);
    const top = columnHeights[columnIndex];

    positions.push({
      image,
      left,
      top,
      width: actualColumnWidth,
      height: imageHeight,
      originalIndex: index,
    });

    // 열 높이 업데이트 (이미지 높이 + 간격)
    columnHeights[columnIndex] += imageHeight + gap;
  });

  const totalHeight = Math.max(...columnHeights) - gap; // 마지막 gap 제거

  return { positions, totalHeight };
}

// 스켈레톤 컴포넌트
function SkeletonGrid() {
  return (
    <div className="w-[85%] max-w-[1700px] mx-auto grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4 py-8">
      {SKELETON_RATIOS.map((ratio, i) => (
        <div
          key={i}
          className="bg-gray-200 rounded-xl animate-pulse"
          style={{ aspectRatio: ratio }}
        />
      ))}
    </div>
  );
}

// 빈 상태 컴포넌트
function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-gray-500">
      <p className="text-lg font-medium">이미지가 없습니다</p>
    </div>
  );
}

import { useTaskStore } from "@/stores/useTaskStore";
import { cn } from "@/types/utils";

// Pinterest 스타일 가상화 Masonry
function VirtualizedMasonry({
  images,
  onEndReached,
}: {
  images: GalleryImageSummary[];
  onEndReached?: () => void;
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  // SSR 대응: 초기화 시 window 객체 직접 참조 금지 (Hydration Mismatch 방지)
  const [containerOffsetTop, setContainerOffsetTop] = useState(0);
  const [containerWidth, setContainerWidth] = useState(0);
  const [scrollTop, setScrollTop] = useState(0);
  const [viewportHeight, setViewportHeight] = useState(800);

  // 전역 모달 상태 관리
  const { setSelectedJobId } = useTaskStore();

  // 레이아웃 치수 측정 함수 (마운트 시 및 리사이즈 시 호출)
  const updateLayout = useCallback(() => {
    const container = containerRef.current;
    if (!container) return;
    
    const rect = container.getBoundingClientRect();
    setContainerOffsetTop(rect.top + window.scrollY);
    setContainerWidth(rect.width);
    setScrollTop(window.scrollY);
    setViewportHeight(window.innerHeight);
  }, []);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    // 마운트 직후 즉시 측정하여 0 크기 방지
    updateLayout();

    // 브라우저 리사이즈 감지
    const observer = new ResizeObserver(() => {
      updateLayout();
    });

    observer.observe(container);
    return () => observer.disconnect();
  }, [updateLayout]);

  // 스크롤 및 뷰포트 높이 추적
  useEffect(() => {
    const handleScroll = () => {
      setScrollTop(window.scrollY);
    };

    const handleResize = () => {
      setViewportHeight(window.innerHeight);
    };

    handleResize();
    window.addEventListener("scroll", handleScroll, { passive: true });
    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("scroll", handleScroll);
      window.removeEventListener("resize", handleResize);
    };
  }, []);

// Masonry 위치 계산
  const { positions, totalHeight } = useMemo(
    () => calculateMasonryPositions(images, containerWidth, COLUMN_WIDTH, GAP),
    [images, containerWidth],
  );

  // 가장 높은 유사도 점수를 가진 이미지 ID 찾기 (Best Match)
  const bestMatchId = useMemo(() => {
    // 점수가 있는 이미지가 하나라도 있어야 함
    const candidates = images.filter(img => img.similarityScore !== undefined && img.similarityScore > 0);
    if (candidates.length === 0) return null;

    // 점수 내림차순 정렬 후 첫 번째 아이템 반환
    return candidates.sort((a, b) => (b.similarityScore ?? 0) - (a.similarityScore ?? 0))[0].id;
  }, [images]);

  // 뷰포트 내 보이는 이미지 필터링 (가상화 보정)
  const visibleImages: PositionedImage[] = useMemo(() => {
    const overscan = 500; // 버퍼 확장
    const relativeScrollTop = Math.max(0, scrollTop - containerOffsetTop);

    const viewTop = relativeScrollTop - overscan;
    const viewBottom = relativeScrollTop + viewportHeight + overscan;

    const filtered = positions.filter((pos) => {
      const itemTop = pos.top;
      const itemBottom = pos.top + pos.height;
      return itemBottom >= viewTop && itemTop <= viewBottom;
    });
    
    return filtered;
  }, [positions, scrollTop, viewportHeight, containerOffsetTop, containerWidth]);

  // 무한 스크롤 감지 (보정된 스크롤 기준)
  useEffect(() => {
    if (!onEndReached || totalHeight === 0) return;

    const relativeScrollTop = Math.max(0, scrollTop - containerOffsetTop);
    const scrollPosition = relativeScrollTop + viewportHeight;

    if (scrollPosition >= totalHeight - 300) {
      onEndReached();
    }
  }, [
    scrollTop,
    viewportHeight,
    totalHeight,
    onEndReached,
    containerOffsetTop,
  ]);

  return (
    <div className="w-[85%] max-w-[1700px] mx-auto py-8">
      <div ref={containerRef}>
        <div
          style={{
            position: 'relative',
            width: '100%',
            height: totalHeight,
          }}
        >
          {visibleImages.map((pos) => {
            const isBestMatch = pos.image.id === bestMatchId;



            return (
              <div
                key={pos.image.id}
                className={cn(
                  "transition-all duration-500 ease-in-out",
                  isBestMatch ? "z-20 scale-[1.02]" : "z-0 hover:z-10"
                )}
                style={{
                  position: "absolute",
                  left: pos.left,
                  top: pos.top,
                  width: pos.width,
                  height: pos.height,
                }}
              >
                {/* Glow Effect Layer (Behind) */}
                {isBestMatch && (
                  <div className="absolute -inset-[4px] rounded-xl z-0">
                    <GlowingEffect
                      spread={60}
                      glow={true}
                      disabled={false}
                      proximity={64}
                      inactiveZone={0.01}
                      borderWidth={4}
                      blur={5}
                      autoplay={true}
                      movementDuration={2.6}
                    />
                  </div>
                )}

                {/* Content Layer (Front) */}
                <div className="relative w-full h-full rounded-xl overflow-hidden z-10 shadow-sm bg-background">
                  {pos.image.assetType === ASSET_TYPE.VIDEO ? (
                    <VideoCard
                      src={pos.image.src}
                      aspectRatio={`${pos.image.width}/${pos.image.height}`}
                      onClick={() => setSelectedJobId(pos.image.jobId)}
                      similarityScore={pos.image.similarityScore}
                      overlay={
                        <GalleryImageOverlay
                          author={pos.image.author}
                          likes={pos.image.likes ?? 0}
                          similarityScore={pos.image.similarityScore}
                        />
                      }
                    />
                  ) : (
                    <ImageCard
                      src={pos.image.src}
                      alt={`이미지 ${pos.image.id}`}
                      aspectRatio={`${pos.image.width}/${pos.image.height}`}
                      blurDataURL={pos.image.blurDataURL}
                      priority={pos.originalIndex < 10}
                      onClick={() => setSelectedJobId(pos.image.jobId)}
                      similarityScore={pos.image.similarityScore}
                      overlay={
                        <GalleryImageOverlay
                          author={pos.image.author}
                          likes={pos.image.likes ?? 0}
                          similarityScore={pos.image.similarityScore}
                        />
                      }
                    />
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

export function MasonryGrid({
  images,
  isLoading = false,
  onEndReached,
}: MasonryGridProps) {
  // 전역 모달 상태 관리 (상위로 이동)
  const { selectedJobId, setSelectedJobId } = useTaskStore();

  // 네비게이션 로직 (상위로 이동)
  const handleNavigate = (direction: "prev" | "next") => {
    if (!selectedJobId) return;

    const currentIndex = images.findIndex(
      (img) => img.jobId === selectedJobId || img.id === selectedJobId,
    );
    if (currentIndex === -1) return;

    if (direction === "prev" && currentIndex > 0) {
      setSelectedJobId(images[currentIndex - 1].jobId);
    } else if (direction === "next" && currentIndex < images.length - 1) {
      setSelectedJobId(images[currentIndex + 1].jobId);
    }
  };

  const content = (() => {
    if (isLoading && images.length === 0) {
      return <SkeletonGrid />;
    }

    if (images.length === 0) {
      return <EmptyState />;
    }

    return <VirtualizedMasonry images={images} onEndReached={onEndReached} />;
  })();

  return (
    <>
      {content}

      {/* 이미지 상세 모달 (항상 렌더링) */}
      <ImageDetailModal
        imageId={selectedJobId}
        onClose={() => setSelectedJobId(null)}
        onNavigate={images.length > 0 ? handleNavigate : undefined}
      />
    </>
  );
}
