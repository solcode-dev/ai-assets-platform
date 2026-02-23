'use client';

import { Fragment, useEffect } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { X, ChevronLeft, ChevronRight } from 'lucide-react';
import Image from 'next/image';
import { useAssetDetail } from '@/hooks/useAssetDetail';
import { AssetMetadata } from './AssetMetadata';
import { ASSET_STATUS, ASSET_TYPE } from '@/types/image';

interface ImageDetailModalProps {
  imageId: string | null;
  onClose: () => void;
  onNavigate?: (direction: 'prev' | 'next') => void;
}

export function ImageDetailModal({ imageId, onClose, onNavigate }: ImageDetailModalProps) {
  const { data: asset, isLoading, error } = useAssetDetail(imageId);

  // 키보드 네비게이션
  useEffect(() => {
    if (!imageId) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      // 인풋이나 텍스트에어리어에서 입력 중일 때는 화살표 키 네비게이션 무시
      const target = e.target as HTMLElement;
      if (
        target.tagName === 'INPUT' || 
        target.tagName === 'TEXTAREA' || 
        target.isContentEditable
      ) {
        return;
      }

      // ESC는 Dialog가 자동 처리
      if (e.key === 'ArrowLeft' && onNavigate) {
        e.preventDefault();
        onNavigate('prev');
      } else if (e.key === 'ArrowRight' && onNavigate) {
        e.preventDefault();
        onNavigate('next');
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [imageId, onNavigate]);

  // pending 상태 방어 로직 (생성 중이거나 처리 중인 경우)
  const isPending = asset?.status === ASSET_STATUS.PENDING || asset?.status === ASSET_STATUS.PROCESSING;

  // 기본 Blur 데이터 (회색 배경)
  const DEFAULT_BLUR_DATA_URL = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mN8/+F9PQAI8AKp2of4ngAAAABJRU5ErkJggg==';

  return (
    <Transition appear show={!!imageId} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={onClose}>
        {/* 접근성: 스크린 리더용 제목 */}
        <Dialog.Title className="sr-only">이미지 상세 정보</Dialog.Title>

        {/* 배경 오버레이 */}
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black/90" aria-hidden="true" />
        </Transition.Child>

        {/* 모달 컨테이너 */}
        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 scale-95"
              enterTo="opacity-100 scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 scale-100"
              leaveTo="opacity-0 scale-95"
            >
              <Dialog.Panel className="relative w-full max-w-7xl transform overflow-hidden rounded-2xl bg-white dark:bg-gray-900 shadow-2xl transition-all">
                {/* Close 버튼 (우측 상단) */}
                <button
                  onClick={onClose}
                  className="absolute top-4 right-4 z-10 p-2 rounded-full bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
                  aria-label="모달 닫기"
                >
                  <X size={24} className="text-gray-700 dark:text-gray-300" />
                </button>

                {/* 네비게이션 버튼 (좌우) */}
                {onNavigate && (
                  <>
                    <button
                      onClick={() => onNavigate('prev')}
                      className="absolute left-4 top-1/2 -translate-y-1/2 z-10 p-3 rounded-full bg-gray-100/80 dark:bg-gray-800/80 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors backdrop-blur-sm"
                      aria-label="이전 이미지"
                    >
                      <ChevronLeft size={24} className="text-gray-700 dark:text-gray-300" />
                    </button>
                    <button
                      onClick={() => onNavigate('next')}
                      className="absolute right-4 top-1/2 -translate-y-1/2 z-10 p-3 rounded-full bg-gray-100/80 dark:bg-gray-800/80 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors backdrop-blur-sm"
                      aria-label="다음 이미지"
                    >
                      <ChevronRight size={24} className="text-gray-700 dark:text-gray-300" />
                    </button>
                  </>
                )}

                {/* 로딩 상태 (initialData가 없을 때만 표시) */}
                {isLoading && !asset && (
                  <div className="flex items-center justify-center h-[500px]">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
                  </div>
                )}

                {/* 에러 상태 */}
                {error && (
                  <div className="flex items-center justify-center h-96">
                    <p className="text-red-500">이미지를 불러올 수 없습니다.</p>
                  </div>
                )}

                {/* pending 상태 방어 */}
                {isPending && (
                  <div className="flex flex-col items-center justify-center h-96 space-y-4">
                    <p className="text-yellow-500 font-semibold">이 이미지는 아직 생성 중입니다.</p>
                    <p className="text-gray-500 text-sm">완료된 이미지만 확인할 수 있습니다.</p>
                    <button
                      onClick={onClose}
                      className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                    >
                      갤러리로 돌아가기
                    </button>
                  </div>
                )}

                {/* 콘텐츠 */}
                {asset && !isPending && asset.src && (
                  <div className="flex flex-col lg:flex-row">
                    {/* 이미지 영역 */}
                    <div className="flex-1 lg:w-[65%] p-8 flex items-center justify-center bg-gray-50 dark:bg-gray-800 relative">
                      <div 
                        className="relative w-full h-full max-h-[80vh]"
                        style={{ aspectRatio: `${asset.width} / ${asset.height}` }}
                      >
                        {asset.assetType === ASSET_TYPE.VIDEO ? (
                          <video
                            src={asset.src}
                            className="absolute inset-0 w-full h-full object-contain rounded-lg"
                            controls
                            autoPlay
                            loop
                            playsInline
                          />
                        ) : (
                          <Image
                            src={asset.src}
                            alt={asset.prompt || 'Generated image'}
                            fill
                            className="object-contain rounded-lg"
                            sizes="(max-width: 768px) 100vw, 65vw"
                            priority
                            placeholder="blur"
                            blurDataURL={asset.blurDataURL || DEFAULT_BLUR_DATA_URL}
                          />
                        )}
                      </div>
                    </div>

                    {/* 메타데이터 영역 (30-40%) */}
                    <div className="lg:w-[35%] p-8 bg-white dark:bg-gray-900 overflow-y-auto">
                      <AssetMetadata
                        assetId={asset.id}
                        src={asset.src}
                        prompt={asset.prompt || ''}
                        model={asset.model || 'imagen-3.0-fast'}
                        width={asset.width}
                        height={asset.height}
                        createdAt={asset.createdAt}
                        assetType={asset.assetType || 'IMAGE'}
                      />
                    </div>
                  </div>
                )}
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  );
}

