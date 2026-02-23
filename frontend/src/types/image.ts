// 필터 상수 (오타 방지 및 확장 용이)
export const FILTERS = {
  ALL: 'all',
  STYLES: 'styles',
  IMAGES: 'images',
  VIDEOS: 'videos',
} as const;

export type FilterType = typeof FILTERS[keyof typeof FILTERS];

// 탭 타입
export const TABS = { TOP_DAY: 'top-day', LIKES: 'likes' } as const;
export type TabType = typeof TABS[keyof typeof TABS];

// 작업 상태 상수
export const ASSET_STATUS = {
  PENDING: 'PENDING',
  PROCESSING: 'PROCESSING',
  COMPLETED: 'COMPLETED',
  FAILED: 'FAILED',
} as const;

export type AssetStatusType = typeof ASSET_STATUS[keyof typeof ASSET_STATUS];

// 에셋 타입 상수
export const ASSET_TYPE = {
  IMAGE: 'IMAGE',
  VIDEO: 'VIDEO',
} as const;

export type AssetType = typeof ASSET_TYPE[keyof typeof ASSET_TYPE];

// 리스트 조회용 경량 DTO (Over-fetching 방지)
export interface GalleryImageSummary {
  readonly id: string;
  readonly jobId: string; // 알림 연동을 위한 전역 ID
  readonly src: string;
  readonly width: number;
  readonly height: number;
  readonly prompt: string;
  readonly model: string;
  readonly createdAt: string;
  readonly blurDataURL?: string;
  readonly status: AssetStatusType;
  readonly assetType: AssetType;
  // 오버레이 표시용 (선택적)
  readonly author?: string;
  readonly likes?: number;
  readonly similarityScore?: number;
}

// 상세 조회용 전체 모델
export interface GalleryImage extends GalleryImageSummary {
  readonly alt: string;
  readonly author?: string;
  readonly likes: number;
  readonly tags: string[];
  readonly category: FilterType;
}

// 커서 기반 페이지네이션 응답
export interface PaginatedResponse<T> {
  readonly data: T[];
  readonly nextCursor: string | null;  // null이면 마지막 페이지
  readonly hasMore: boolean;
}

// 검색 상태 (URL SearchParams 기반)
export interface SearchParams {
  readonly query?: string;
  readonly filter?: FilterType;
  readonly tab?: TabType;
}

// 생성 모드 타입
export type GenerationMode = 'text-to-image' | 'text-to-video' | 'image-to-video';

