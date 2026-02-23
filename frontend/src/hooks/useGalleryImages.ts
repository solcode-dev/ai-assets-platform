import { useInfiniteQuery } from "@tanstack/react-query";
import { FilterType, GalleryImageSummary, ASSET_STATUS, AssetStatusType, ASSET_TYPE } from '@/types/image';

interface UseGalleryImagesParams {
  filter: FilterType;
  query?: string;
  hybrid?: boolean;
}

// 백엔드 API 응답의 원본 데이터 구조 정의
interface RawAssetResponse {
  id: number;
  job_id?: string;
  result_url?: string;
  file_path?: string;
  src?: string;
  asset_type: 'IMAGE' | 'VIDEO';
  created_at: string;
  status: string;
  width?: number;
  height?: number;
  prompt: string;
  model: string;
  similarity_score?: number;
  [key: string]: unknown;
}

/**
 * 백엔드 API로부터 이미지 목록을 가져오는 함수
 */
const fetchImages = async ({
  filter,
  query,
  hybrid = true,
  cursor,
}: {
  filter: FilterType;
  query?: string;
  hybrid?: boolean;
  cursor?: string;
}) => {
  let url = '/api/assets';
  const params = new URLSearchParams({ filter });
  if (cursor) params.set('cursor', cursor);

  // 검색 쿼리가 있는 경우 전역 검색 엔드포인트 사용
  // 문자열 "undefined"나 빈 공백은 무시하여 불필요한 검색 방지
  if (query && query !== 'undefined' && query.trim() !== '') {
    url = '/api/assets/search';
    params.set('q', query);
    params.set('hybrid', String(hybrid));
    // 검색 엔드포인트는 현재 커서 페이징을 지원하지 않으므로 cursor 삭제
    params.delete('cursor');
  }

  const res = await fetch(`${url}?${params}`);
  if (!res.ok) throw new Error('에셋 목록을 불러오는데 실패했습니다.');
  
  const data = await res.json();
  // console.log('[useGalleryImages] Raw API Data sample:', Array.isArray(data) ? data.slice(0, 1) : (data.data?.slice(0, 1) || data.results?.slice(0, 1)));

  // 검색 결과는 배열로 직접 오고, 일반 목록은 { success, data, nextCursor } 또는 { data, nextCursor } 형태로 올 수 있음
  let items = [];
  if (Array.isArray(data)) {
    items = data;
  } else if (data.data && Array.isArray(data.data)) {
    items = data.data;
  } else if (data.results && Array.isArray(data.results)) {
    items = data.results;
  }
  
  // COMPLETED 상태인 에셋만 필터링 (생성 중인 에셋은 갤러리에서 제외)
  const completedItems = items.filter(
    (item: RawAssetResponse) => item.status === ASSET_STATUS.COMPLETED
  );
  
  // console.log(`[useGalleryImages] Extracted ${items.length} items, found ${completedItems.length} COMPLETED.`);

  // 백엔드 데이터 매핑 (Snake Case -> Camel Case 및 필수 필드 보정)
  const mappedItems: GalleryImageSummary[] = completedItems.map((item: RawAssetResponse) => {
    const src = item.src || item.result_url || item.file_path || '';
    if (!src) console.warn(`[useGalleryImages] No image source for asset ID: ${item.id}`, item);
    
    // 에셋 타입 판별 (백엔드 필드 + 파일 확장자 기반으로 더 정확하게 판별)
    const isVideo = (item.asset_type as string) === 'VIDEO' || /\.(mp4|webm|mov)$/i.test(src);
    
    return {
      id: String(item.id),
      jobId: item.job_id || String(item.id),
      src,
      width: item.width || 1024,
      height: item.height || 1024,
      prompt: item.prompt || '',
      model: item.model || '',
      assetType: isVideo ? ASSET_TYPE.VIDEO : ASSET_TYPE.IMAGE,
      status: item.status as AssetStatusType,
      createdAt: item.created_at,
      similarityScore: item.similarity_score,
    };
  });

  console.log('[useGalleryImages] Final Mapped Items sample:', mappedItems.slice(0, 2));

  return {
    data: mappedItems,
    nextCursor: Array.isArray(data) ? undefined : data.nextCursor,
  };
};

export function useGalleryImages({ filter, query, hybrid = true }: UseGalleryImagesParams) {
  const infiniteQuery = useInfiniteQuery({
    queryKey: ['assets', filter, query, hybrid],
    queryFn: ({ pageParam }) => fetchImages({ filter, query, hybrid, cursor: pageParam }),
    getNextPageParam: (lastPage) => lastPage.nextCursor,
    initialPageParam: undefined as string | undefined,
    staleTime: 1 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
  });

  return {
    images: infiniteQuery.data?.pages.flatMap((page) => page.data) ?? [],
    ...infiniteQuery,
  };
}
