'use client';

import { useRoutingStore } from '@/stores/routingStore';
import { Button } from '@/components/ui/button';
import { X } from 'lucide-react';

/**
 * SelectedJobCenter Component
 *
 * Displays the currently selected job center for routing analysis
 * with an option to deselect it.
 */
export function SelectedJobCenter() {
  const selectedJobCenter = useRoutingStore((state) => state.selectedJobCenter);
  const setSelectedJobCenter = useRoutingStore((state) => state.setSelectedJobCenter);

  if (!selectedJobCenter) {
    return (
      <div className="text-sm text-gray-500 italic">
        Click a job center on the map to select it for routing analysis
      </div>
    );
  }

  return (
    <div className="bg-green-50 border border-green-200 rounded-lg p-3">
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <div className="text-sm font-semibold text-green-900 mb-1">
            Selected for Routing
          </div>
          <div className="text-sm text-green-800 font-medium">
            {selectedJobCenter.name_en || selectedJobCenter.name_he}
          </div>
          {selectedJobCenter.estimated_employees && (
            <div className="text-xs text-green-700 mt-1">
              {selectedJobCenter.estimated_employees.toLocaleString()} employees
            </div>
          )}
          <div className="text-xs text-green-600 mt-1">
            {selectedJobCenter.type}
          </div>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setSelectedJobCenter(null)}
          className="h-6 w-6 p-0 text-green-700 hover:text-green-900 hover:bg-green-100"
        >
          <X className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
