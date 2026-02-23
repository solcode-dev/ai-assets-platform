import { NextRequest, NextResponse } from "next/server";
import {
  GalleryImageSummary,
  PaginatedResponse,
  AssetStatusType,
  AssetType,
} from "@/types/image";

const PAGE_SIZE = 20;

interface BackendAsset {
  id: number;
  file_path: string | null;
  width: number | null;
  height: number | null;
  result_url: string | null;
  status: AssetStatusType;
  asset_type: AssetType;
  prompt: string;
  model: string;
  created_at: string;
  job_id: string;
}

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const cursor = searchParams.get("cursor");

  // 프론트엔드 infinite query의 cursor를 그대로 백엔드에 전달 (ID 기반 커서)
  const limit = PAGE_SIZE;

  try {
    const backendUrl =
      process.env.INTERNAL_API_URL ||
      process.env.NEXT_PUBLIC_API_URL ||
      "http://localhost:8000";

    const params = new URLSearchParams();
    if (cursor) params.append("cursor", cursor);
    params.append("limit", limit.toString());

    const targetUrl = `${backendUrl}/api/assets?${params.toString()}`;
    console.log(`[API/Images] Fetching from: ${targetUrl}`);

    const res = await fetch(targetUrl, {
      cache: "no-store",
    });

    console.log(`[API/Images] Backend response status: ${res.status}`);

    if (!res.ok) {
      throw new Error(`Backend API error: ${res.status}`);
    }

    const assets: BackendAsset[] = await res.json();
    console.log(`[API/Images] Received ${assets.length} assets from backend`);

    const images: GalleryImageSummary[] = assets.map((asset) => {
      const src = asset.result_url || asset.file_path || '';
      
      return {
        id: String(asset.id),
        src, // 백엔드에서 준 상대 경로(/storage/...) 그대로 사용
        width: asset.width || 1024, 
        height: asset.height || 1024,
        status: asset.status, 
        assetType: asset.asset_type, // 백엔드는 asset_type 사용
        prompt: asset.prompt,
        model: asset.model,
        createdAt: asset.created_at,
        jobId: asset.job_id,
      };
    }).filter(img => {
        if (img.src === '') console.warn(`[API/Images] Filtered out asset ${img.id} due to empty src`);
        return img.src !== '';
    });
    console.log(`[API/Images] Returning ${images.length} images to frontend`);

    // 다음 커서: 마지막 아이템의 ID
    const nextCursor =
      assets.length === limit ? String(assets[assets.length - 1].id) : null;
    const hasMore = assets.length === limit;

    const response: PaginatedResponse<GalleryImageSummary> = {
      data: images,
      nextCursor,
      hasMore,
    };

    return NextResponse.json(response);
  } catch (error) {
    console.error("Failed to fetch images from backend:", error);
    return NextResponse.json(
      { data: [], nextCursor: null, hasMore: false },
      { status: 500 },
    );
  }
}
