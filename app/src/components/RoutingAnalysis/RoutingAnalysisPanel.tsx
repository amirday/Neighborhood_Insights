'use client';

import { JobCenter } from '@/types';

interface RoutingAnalysisPanelProps {
  selectedJobCenter: JobCenter | null;
  routesCalculationEnabled: boolean;
  onToggleRoutesCalculation: (enabled: boolean) => void;
  routesLoading: boolean;
  routingStats: any | null;
  routingError: string | null;
  onCalculateRoutes: () => void;
}

export function RoutingAnalysisPanel({
  selectedJobCenter,
  routesCalculationEnabled,
  onToggleRoutesCalculation,
  routesLoading,
  routingStats,
  routingError,
  onCalculateRoutes,
}: RoutingAnalysisPanelProps) {
  if (!selectedJobCenter) return null;

  return (
    <div
      className="fixed left-4 lg:left-6 bg-emerald-50/95 backdrop-blur-sm border border-emerald-200 rounded-xl shadow-md p-4"
      style={{
        top: 'calc(var(--header-height) + 1rem)',
        zIndex: 'var(--z-filter-panel)',
        maxWidth: 'min(20rem, calc(100vw - 2rem))',
      }}
    >
      <div className="flex items-center justify-between mb-3">
        <div className="text-sm font-semibold text-gray-900">
          Routing Analysis
        </div>
        {routesLoading && (
          <div className="w-4 h-4 border-2 border-emerald-600 border-t-transparent rounded-full animate-spin" />
        )}
      </div>

      {/* Checkbox */}
      <label className="flex items-start gap-3 cursor-pointer group mb-4">
        <div className="relative">
          <input
            type="checkbox"
            checked={routesCalculationEnabled}
            onChange={(e) => onToggleRoutesCalculation(e.target.checked)}
            className="sr-only"
          />
          <div
            className={`w-5 h-5 rounded border-2 ${
              routesCalculationEnabled
                ? 'bg-emerald-600 border-emerald-600'
                : 'border-gray-300 group-hover:border-emerald-400'
            }`}
          >
            {routesCalculationEnabled && (
              <svg
                className="w-3 h-3 text-white m-0.5"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                  clipRule="evenodd"
                />
              </svg>
            )}
          </div>
        </div>

        <div className="flex-1 min-w-0">
          <div className="text-sm font-medium text-gray-900">
            Calculate Routes (Driving, Cycling, Walking, Transit)
          </div>
          <p className="text-xs text-gray-600 mt-1">
            Uses OSRM for driving/cycling/walking; transit is approximated from driving.
          </p>
        </div>
      </label>

      {/* Calculate Button */}
      <button
        onClick={onCalculateRoutes}
        disabled={!routesCalculationEnabled || routesLoading}
        className="w-full text-sm py-2.5 px-4 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
      >
        {routesLoading ? 'Calculating…' : 'Calculate Routes'}
      </button>

      {/* Error Display */}
      {routingError && (
        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-start gap-2">
            <svg className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
            <div className="flex-1">
              <div className="text-xs font-semibold text-red-800 mb-1">Routing Failed</div>
              <div className="text-xs text-red-700">{routingError}</div>
              <div className="text-xs text-red-600 mt-2 italic">
                Tip: Check if OSRM API is accessible or use a local routing server
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Success Statistics */}
      {routingStats && !routingError && (
        <div className={`mt-4 p-3 border rounded-lg ${
          routingStats.success_rate > 50
            ? 'bg-green-50 border-green-200'
            : 'bg-yellow-50 border-yellow-200'
        }`}>
          <div className="flex items-center gap-2 mb-2">
            <svg className={`w-5 h-5 ${
              routingStats.success_rate > 50 ? 'text-green-600' : 'text-yellow-600'
            }`} fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            <div className="text-xs font-semibold text-gray-900">Routing Complete</div>
          </div>

          {/* Overall Stats */}
          <div className="grid grid-cols-2 gap-2 mb-3">
            <div className="text-xs">
              <div className="text-gray-600">Success Rate</div>
              <div className={`font-semibold ${
                routingStats.success_rate > 50 ? 'text-green-700' : 'text-yellow-700'
              }`}>
                {routingStats.success_rate}%
              </div>
            </div>
            <div className="text-xs">
              <div className="text-gray-600">Total Routes</div>
              <div className="font-semibold text-gray-900">
                {routingStats.successful} / {routingStats.total_requests}
              </div>
            </div>
          </div>

          {/* Per-Mode Stats */}
          <div className="text-xs space-y-1.5 border-t border-gray-200 pt-2">
            <div className="font-medium text-gray-700 mb-1">By Mode:</div>
            {Object.entries(routingStats.by_mode || {}).map(([mode, stats]: [string, any]) => (
              <div key={mode} className="flex justify-between items-center">
                <span className="text-gray-600 capitalize">{mode}:</span>
                <span className={`font-medium ${
                  stats.success_rate > 50 ? 'text-green-700' : 'text-red-600'
                }`}>
                  {stats.successful}/{stats.successful + stats.failed} ({stats.success_rate}%)
                </span>
              </div>
            ))}
          </div>

          {/* Warning if low success rate */}
          {routingStats.success_rate < 50 && (
            <div className="mt-3 pt-2 border-t border-yellow-200">
              <div className="text-xs text-yellow-800 italic">
                ⚠️ Low success rate may indicate OSRM API issues
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
