import { useQuery, useQueryClient, InfiniteData } from "@tanstack/react-query";
import { GalleryImageSummary, PaginatedResponse } from "@/types/image";

async function fetchAssetDetail(assetId: string): Promise<GalleryImageSummary> {
  const response = await fetch(`/api/assets/job/${assetId}`);
  
  if (!response.ok) {
    throw new Error("Failed to fetch asset details");
  }

  const data = await response.json();

  // 백엔드(Snake Case) -> 프론트엔드(Camel Case) 매핑
  return {
    ...data,
    id: String(data.id),
    jobId: data.job_id, // 매핑 추가
    src: data.result_url || data.file_path || '',
    assetType: data.asset_type,
    createdAt: data.created_at,
  };
}

export function useAssetDetail(assetId: string | null) {
  const queryClient = useQueryClient();

  // initialData 최적화: 갤러리 쿼리 캐시에서 데이터 가져오기
  const getInitialData = (): GalleryImageSummary | undefined => {
    if (!assetId) return undefined;

    // 갤러리 쿼리에서 해당 ID의 데이터 찾기
    const queries = queryClient.getQueriesData<InfiniteData<PaginatedResponse<GalleryImageSummary>>>({ 
      queryKey: ['assets'] 
    });

    for (const [, infiniteData] of queries) {
      if (infiniteData?.pages) {
        for (const page of infiniteData.pages) {
          const found = page.data?.find((item: GalleryImageSummary) => item.jobId === assetId || item.id === assetId);
          if (found) return found;
        }
      }
    }

    return undefined;
  };

  return useQuery({
    queryKey: ["asset-detail", assetId],
    queryFn: () => fetchAssetDetail(assetId!),
    enabled: !!assetId,
    staleTime: 5 * 60 * 1000, // 5분
    initialData: getInitialData(), // 캐시된 데이터 즉시 표시
  });
}
