import { GenerationContainer } from '@/components/generation/GenerationContainer';
import { GalleryClient } from '@/components/gallery/GalleryClient';
import { FILTERS, FilterType } from '@/types/image';

interface PageProps {
  searchParams: Promise<{ filter?: string; q?: string; hybrid?: string }>;
}

export default async function GalleryPage(props: PageProps) {
  const searchParams = await props.searchParams;
  const filter = (searchParams.filter as FilterType) ?? FILTERS.IMAGES;
  const query = searchParams.q;
  const hybrid = searchParams.hybrid !== 'false'; // 기본값 true

  return (
    <>
      <div className="mb-12 pt-8">
        <GenerationContainer initialPrompt={query} />
      </div>
      <GalleryClient filter={filter} query={query} hybrid={hybrid} />
    </>
  );
}
