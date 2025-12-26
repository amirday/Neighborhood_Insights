'use client';

import { useRoutingStore } from '@/stores/routingStore';
import { Button } from '@/components/ui/button';

/**
 * JobCenterQuickActions Component
 *
 * Provides quick action buttons to select all or clear all job center type filters.
 */
export function JobCenterQuickActions() {
  const selectAllJobCenterTypes = useRoutingStore((state) => state.selectAllJobCenterTypes);
  const clearAllJobCenterTypes = useRoutingStore((state) => state.clearAllJobCenterTypes);

  return (
    <div className="flex gap-2">
      <Button
        variant="outline"
        size="sm"
        onClick={selectAllJobCenterTypes}
        className="flex-1"
      >
        Show All
      </Button>
      <Button
        variant="outline"
        size="sm"
        onClick={clearAllJobCenterTypes}
        className="flex-1"
      >
        Hide All
      </Button>
    </div>
  );
}
