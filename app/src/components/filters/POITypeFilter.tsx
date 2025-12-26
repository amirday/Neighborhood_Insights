'use client';

import { usePOIStore } from '@/stores/poiStore';
import { colors } from '@/design-system/tokens/colors';
import { Checkbox } from '@/components/ui/checkbox';

/**
 * POITypeFilter Component
 *
 * Displays checkboxes for each POI type, allowing users to filter
 * which types of POIs are visible on the map.
 */
export function POITypeFilter() {
  const poiTypes = usePOIStore((state) => state.poiTypes);
  const selectedTypes = usePOIStore((state) => state.selectedTypes);
  const toggleType = usePOIStore((state) => state.toggleType);
  const pois = usePOIStore((state) => state.pois);

  if (poiTypes.length === 0) {
    return (
      <div className="text-sm text-gray-500">
        No POI types available
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-semibold text-gray-900">POI Types</h3>

      {poiTypes.map((type) => {
        const count = pois.filter((p) => p.type === type).length;
        const isSelected = selectedTypes.includes(type);
        const poiColor = colors.poi[type as keyof typeof colors.poi] || colors.neutral[600];

        return (
          <div
            key={type}
            className="flex items-center gap-3 cursor-pointer group"
            onClick={() => toggleType(type)}
          >
            {/* Color indicator */}
            <div
              className="w-4 h-4 rounded-full border-2 transition-all"
              style={{
                backgroundColor: isSelected ? poiColor : 'transparent',
                borderColor: poiColor,
              }}
              aria-hidden="true"
            />

            {/* Checkbox */}
            <Checkbox
              checked={isSelected}
              onCheckedChange={(checked) => {
                // Prevent double-toggle since we're handling it in the parent div
              }}
              aria-label={`Toggle ${type} POIs`}
            />

            {/* Label and count */}
            <div className="flex-1 min-w-0">
              <div className="text-sm text-gray-900 capitalize">
                {type.replace('_', ' ')}
              </div>
              <div className="text-xs text-gray-500">
                {count} location{count !== 1 ? 's' : ''}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
