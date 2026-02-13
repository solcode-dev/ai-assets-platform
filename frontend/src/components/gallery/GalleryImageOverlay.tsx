import { Heart } from 'lucide-react';

interface GalleryImageOverlayProps {
  author?: string;
  likes: number;
  similarityScore?: number;
}

export function GalleryImageOverlay({ author, likes, similarityScore }: GalleryImageOverlayProps) {
  return (
    <div className="absolute inset-0 bg-linear-to-t from-black/60 via-transparent to-transparent 
                    opacity-0 group-hover:opacity-100 transition-opacity duration-300">
      <div className="absolute bottom-0 left-0 right-0 p-3 text-white">
        {/* {similarityScore !== undefined && (
          <div className="mb-2 inline-block">
            <span className="bg-indigo-500/90 text-white text-[11px] font-bold px-2 py-1 rounded-md shadow-sm backdrop-blur-md border border-white/10">
              일치율: {Math.round(similarityScore * 100)}%
            </span>
          </div>
        )} */}
        {author && <p className="text-sm font-medium truncate">{author}</p>}
        <div className="flex items-center gap-1 text-xs" aria-label={`좋아요 ${likes}개`}>
          <Heart size={12} fill="currentColor" aria-hidden />
          <span>{likes.toLocaleString()}</span>
        </div>
      </div>
    </div>
  );
}
