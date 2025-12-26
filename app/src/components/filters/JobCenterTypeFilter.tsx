'use client';

import { useRoutingStore } from '@/stores/routingStore';
import { colors } from '@/design-system/tokens/colors';
import { Checkbox } from '@/components/ui/checkbox';

/**
 * JobCenterTypeFilter Component
 *
 * Displays checkboxes for each job center type, allowing users to filter
 * which types of job centers are visible on the map.
 */
export function JobCenterTypeFilter() {
  const jobCenterTypes = useRoutingStore((state) => state.jobCenterTypes);
  const selectedJobCenterTypes = useRoutingStore((state) => state.selectedJobCenterTypes);
  const toggleJobCenterType = useRoutingStore((state) => state.toggleJobCenterType);
  const jobCenters = useRoutingStore((state) => state.jobCenters);

  if (jobCenterTypes.length === 0) {
    return (
      <div className="text-sm text-gray-500">
        No job center types available
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-semibold text-gray-900">Job Center Types</h3>

      {jobCenterTypes.map((type) => {
        const count = jobCenters.filter((c) => c.type === type).length;
        const isSelected = selectedJobCenterTypes.includes(type);
        const jobCenterColor = colors.map.jobCenters; // Red color (#DC2626)

        return (
          <div
            key={type}
            className="flex items-center gap-3 cursor-pointer group"
            onClick={() => toggleJobCenterType(type)}
          >
            {/* Color indicator */}
            <div
              className="w-4 h-4 rounded-full border-2 transition-all"
              style={{
                backgroundColor: isSelected ? jobCenterColor : 'transparent',
                borderColor: jobCenterColor,
              }}
              aria-hidden="true"
            />

            {/* Checkbox */}
            <Checkbox
              checked={isSelected}
              onCheckedChange={(checked) => {
                // Prevent double-toggle since we're handling it in the parent div
              }}
              aria-label={`Toggle ${type} job centers`}
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
