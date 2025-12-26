'use client';

import { usePOIStore } from '@/stores/poiStore';
import { Button } from '@/components/ui/button';

/**
 * QuickActions Component
 *
 * Provides quick action buttons to select all or clear all POI type filters.
 */
export function QuickActions() {
  const selectAllTypes = usePOIStore((state) => state.selectAllTypes);
  const clearAllTypes = usePOIStore((state) => state.clearAllTypes);

  return (
    <div className="flex gap-2">
      <Button
        variant="outline"
        size="sm"
        onClick={selectAllTypes}
        className="flex-1"
      >
        Show All
      </Button>
      <Button
        variant="outline"
        size="sm"
        onClick={clearAllTypes}
        className="flex-1"
      >
        Hide All
      </Button>
    </div>
  );
}
