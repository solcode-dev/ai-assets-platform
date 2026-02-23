import { Palette, Image, Video } from 'lucide-react';
import { FILTERS, FilterType } from '@/types/image';

interface FilterButtonGroupProps {
  current: FilterType;
  onChange: (filter: FilterType) => void;
}

const filterButtons = [
  { id: FILTERS.STYLES, icon: Palette, label: 'Styles' },
  { id: FILTERS.IMAGES, icon: Image, label: 'Images' },
  { id: FILTERS.VIDEOS, icon: Video, label: 'Videos' },
];

export function FilterButtonGroup({ current, onChange }: FilterButtonGroupProps) {
  return (
    <div className="flex bg-gray-100 rounded-full p-1">
      {filterButtons.map((btn) => (
        <button
          key={btn.id}
          onClick={() => onChange(btn.id)}
          className={`
            flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium transition-colors
            ${current === btn.id ? 'bg-white text-black shadow-sm' : 'text-gray-500 hover:text-gray-700'}
          `}
          aria-pressed={current === btn.id}
        >
          <btn.icon size={14} />
          {btn.label}
        </button>
      ))}
    </div>
  );
}
