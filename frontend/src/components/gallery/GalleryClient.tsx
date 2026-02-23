'use client';

import { MasonryGrid } from './MasonryGrid';
import { useGalleryImages } from '@/hooks/useGalleryImages';
import { ErrorPlaceholder } from '@/components/ui/ErrorPlaceholder';
import { FilterType } from '@/types/image';

interface GalleryClientProps {
  filter: FilterType;
  query?: string;
  hybrid?: boolean;
}

export function GalleryClient({ filter, query, hybrid = true }: GalleryClientProps) {
  const {
    images,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    isLoading,
    isError,
    refetch,
  } = useGalleryImages({ filter, query, hybrid });

  // 에러 처리: 첫 로드 실패 시 전체 에러 UI
  if (isError && images.length === 0) {
    return <ErrorPlaceholder onRetry={() => refetch()} />;
  }

  return (
    <section aria-label="이미지 갤러리">
      <MasonryGrid 
        images={images} 
        isLoading={isLoading}
        onEndReached={() => hasNextPage && !isFetchingNextPage && fetchNextPage()}
      />
      {isFetchingNextPage && <p className="text-center py-4 text-gray-400">로딩 중...</p>}
      {!hasNextPage && images.length > 0 && (
        <p className="text-center py-8 text-gray-400">모든 이미지를 불러왔습니다</p>
      )}
    </section>
  );
}
