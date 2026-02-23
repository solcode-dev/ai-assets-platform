import { useState } from 'react';
import { toast } from 'sonner';
import { ASSET_TYPE, AssetType } from '@/types/image';

interface UseAssetDownloadOptions {
  assetId: string;
  assetType: AssetType;
}

interface UseAssetDownloadReturn {
  isDownloading: boolean;
  download: () => Promise<void>;
}

/**
 * 메모리 효율적인 에셋 다운로드 훅
 * 
 * **전략 선택**:
 * - 작은 파일 (이미지): blob() 사용으로 더 나은 UX (팝업 없음)
 * - 큰 파일 (영상): 직접 링크로 메모리 오버플로우 방지
 * 
 * **왜 대용량 파일에 blob()을 사용하지 않나?**
 * - blob()은 파일 전체를 RAM에 로드함
 * - 500MB 영상 = 500MB RAM 소비
 * - 브라우저 탭 크래시 또는 OOM 에러 발생 가능
 */
export function useAssetDownload({
  assetId,
  assetType,
}: UseAssetDownloadOptions): UseAssetDownloadReturn {
  const [isDownloading, setIsDownloading] = useState(false);

  const download = async () => {
    // 1. 중복 클릭 방지
    if (isDownloading) return;
    setIsDownloading(true);

    try {
      const downloadUrl = `/api/assets/${assetId}/download`;
      const extension = assetType === ASSET_TYPE.VIDEO ? 'mp4' : 'png';
      const filename = `generated-${assetId}.${extension}`;

      // 2. 메모리 효율적 방식: 직접 링크
      // 브라우저가 자동으로 스트리밍 처리
      // RAM 소비 없음, 모든 파일 크기에 대응 가능
      const a = document.createElement('a');
      a.href = downloadUrl;
      a.download = filename;
      
      // 3. 다운로드 실행
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);

      // 4. 성공 피드백
      toast.success('다운로드가 시작되었습니다.');
    } catch (error) {
      // 5. 에러 피드백
      console.error('Download error:', error);
      toast.error(
        error instanceof Error ? error.message : '다운로드 중 오류가 발생했습니다.'
      );
    } finally {
      // 6. 로딩 상태 해제
      setIsDownloading(false);
    }
  };

  return {
    isDownloading,
    download,
  };
}

