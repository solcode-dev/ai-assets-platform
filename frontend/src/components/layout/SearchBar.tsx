'use client';

import { useState, useCallback } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useDebouncedCallback } from 'use-debounce';
import { FILTERS, FilterType, TABS, TabType } from '@/types/image';
import { FilterButtonGroup } from './FilterButtonGroup';
import { NotificationCenter } from './NotificationCenter';

export function SearchBar() {
  const router = useRouter();
  const searchParams = useSearchParams();
  
  const currentFilter = (searchParams.get('filter') as FilterType) ?? FILTERS.IMAGES;
  const currentTab = (searchParams.get('tab') as TabType) ?? TABS.TOP_DAY;
  
  // URL에서 하이브리드 모드 상태 가져오기 (기본값 true)
  const isHybrid = searchParams.get('hybrid') !== 'false';
  
  const [searchInput, setSearchInput] = useState(searchParams.get('q') ?? '');
  
  const updateParams = useCallback((key: string, value?: string | null) => {
    const params = new URLSearchParams(searchParams.toString());
    
    // 값이 없거나, 빈 문자열이거나, 실수로 들어온 'undefined' 문자열인 경우 파라미터 삭제
    if (!value || value === 'undefined' || value.trim() === '') {
      params.delete(key);
    } else {
      params.set(key, value);
    }
    
    router.push(`?${params.toString()}`);
  }, [router, searchParams]);

  // 디바운싱: 300ms 후에 URL 업데이트
  const debouncedSearch = useDebouncedCallback((value: string) => {
    updateParams('q', value);
  }, 300);

  // 하이브리드 검색 토글 핸들러
  const handleHybridToggle = () => {
    updateParams('hybrid', isHybrid ? 'false' : 'true');
  };

  return (
    <header className="sticky top-0 bg-white/80 backdrop-blur-xl z-20 border-b border-gray-100 shadow-xs">
      <div className="flex items-center justify-between px-6 py-4">
        {/* 좌측: 탭 & 하이브리드 토글 */}
        <div className="flex items-center gap-8">
          <div className="flex gap-6">
            <button
              onClick={() => updateParams('tab', TABS.TOP_DAY)}
              className={`text-sm font-bold transition-all relative py-1 ${currentTab === TABS.TOP_DAY ? 'text-blue-600' : 'text-gray-400 hover:text-gray-600'}`}
            >
              Top Day
              {currentTab === TABS.TOP_DAY && <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-600 rounded-full" />}
            </button>
            <button
              onClick={() => updateParams('tab', TABS.LIKES)}
              className={`text-sm font-bold transition-all relative py-1 ${currentTab === TABS.LIKES ? 'text-blue-600' : 'text-gray-400 hover:text-gray-600'}`}
            >
              Likes
              {currentTab === TABS.LIKES && <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-600 rounded-full" />}
            </button>
          </div>

          <div className="flex items-center gap-2 pl-4 border-l border-gray-100">
            <div className="relative group/tooltip flex items-center gap-1.5 focus:outline-none" tabIndex={0}>
              <span className={`text-[10px] font-bold uppercase tracking-tight ${isHybrid ? 'text-blue-600' : 'text-gray-400'}`}>
                Hybrid Search
              </span>
              <svg 
                xmlns="http://www.w3.org/2000/svg" 
                width="13" 
                height="13" 
                viewBox="0 0 24 24" 
                fill="none" 
                stroke="currentColor" 
                strokeWidth="2.5" 
                strokeLinecap="round" 
                strokeLinejoin="round" 
                className="text-gray-400 group-hover/tooltip:text-blue-500 transition-colors cursor-help"
              >
                <circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><path d="M12 17h.01"/>
              </svg>

              {/* CSS Tooltip - 위치를 아래쪽(top-full)으로 변경하여 잘림 방지 */}
              <div className="absolute top-full left-1/2 -translate-x-1/2 mt-2 w-64 p-3 bg-gray-900 text-white text-[11px] leading-relaxed rounded-xl shadow-2xl opacity-0 invisible group-hover/tooltip:opacity-100 group-hover/tooltip:visible transition-all duration-200 z-50 pointer-events-none">
                <p className="font-bold text-blue-400 mb-1 text-center">검색 방식 안내</p>
                <div className="space-y-1.5 border-t border-gray-800 pt-2">
                  <p className="text-gray-300">• <span className="text-white font-semibold">하이브리드</span>: 키워드 매칭과 의미 검색의 종합 순위 (복합 점수로 % 표기 불가)</p>
                  <p className="text-gray-300">• <span className="text-white font-semibold">벡터 전용</span>: 의미 중심 일치율 측정 (% 표시 가능)</p>
                </div>
                {/* 말꼬리 아이콘 - 위쪽으로 방향 변경 */}
                <div className="absolute bottom-full left-1/2 -translate-x-1/2 -mb-1 border-4 border-transparent border-b-gray-900" />
              </div>
            </div>
            <button 
              onClick={handleHybridToggle}
              className={`w-9 h-5 rounded-full transition-all relative shadow-inner cursor-pointer ${isHybrid ? 'bg-blue-600' : 'bg-gray-200'}`}
            >
              <div className={`absolute top-1 w-3 h-3 bg-white rounded-full shadow-md transition-all ${isHybrid ? 'left-5' : 'left-1'}`} />
            </button>
          </div>
        </div>
        
        {/* 우측: 필터 및 알림 센터 */}
        <div className="flex items-center gap-4">
          <FilterButtonGroup 
            current={currentFilter} 
            onChange={(f) => updateParams('filter', f)} 
          />
          <div className="w-px h-6 bg-gray-100 mx-1" /> {/* 구분선 */}
          <NotificationCenter />
        </div>
      </div>
      
      {/* 검색창 - 디바운싱 적용 */}
      <form role="search" className="px-6 pb-4" onSubmit={(e) => e.preventDefault()}>
        <div className="relative group">
          <input
            type="search"
            value={searchInput}
            onChange={(e) => {
              setSearchInput(e.target.value);
              debouncedSearch(e.target.value);
            }}
            placeholder={isHybrid ? "의미적 검색 + 키워드 검색 (하이브리드)" : "벡터 유사도 검색 전용"}
            aria-label="이미지 검색"
            className="w-full pl-6 pr-12 py-3 rounded-2xl border border-gray-100 bg-gray-50/50 focus:bg-white focus:outline-none focus:ring-4 focus:ring-blue-500/10 focus:border-blue-500 transition-all font-medium text-gray-700"
          />
          <div className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-300 group-focus-within:text-blue-500 transition-colors">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
          </div>
        </div>
      </form>
    </header>
  );
}
