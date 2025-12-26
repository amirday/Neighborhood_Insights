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
      className="fixed grid-bg animate-slide-in-left"
      style={{
        top: 'calc(var(--header-height) + 1.5rem)',
        left: '1.5rem',
        zIndex: 'var(--z-filter-panel)',
        maxWidth: 'min(22rem, calc(100vw - 3rem))',
        background: 'var(--color-surface)',
        border: '4px solid var(--color-border)',
        boxShadow: '8px 8px 0 var(--color-sky-blue)',
        animationDelay: '0.3s',
        opacity: 0,
      }}
    >
      {/* Panel Header */}
      <div
        className="px-6 py-4"
        style={{
          background: 'var(--color-surface)',
          borderBottom: '3px solid var(--color-sky-blue)',
        }}
      >
        <div className="flex items-center justify-between">
          <h2
            className="text-display"
            style={{
              fontSize: '1.5rem',
              color: 'var(--color-text-primary)',
              letterSpacing: '0.05em',
            }}
          >
            ROUTING
          </h2>
          {routesLoading && (
            <div
              className="w-4 h-4 pulse-glow"
              style={{
                background: 'var(--color-mint-green)',
                animation: 'pulse-glow 1s ease-in-out infinite',
              }}
            />
          )}
        </div>
      </div>

      <div className="p-6"  style={{ background: 'var(--color-surface)' }}>

        {/* Checkbox */}
        <label className="flex items-start gap-3 cursor-pointer group mb-5">
          <div className="relative">
            <input
              type="checkbox"
              checked={routesCalculationEnabled}
              onChange={(e) => onToggleRoutesCalculation(e.target.checked)}
              className="sr-only"
            />
            <div
              className="w-6 h-6 transition-standard"
              style={{
                border: `3px solid ${routesCalculationEnabled ? 'var(--color-sky-blue)' : 'var(--color-border)'}`,
                background: routesCalculationEnabled ? 'var(--color-sky-blue)' : 'transparent',
              }}
            >
              {routesCalculationEnabled && (
                <svg
                  className="w-4 h-4 m-0.5"
                  fill="var(--color-surface)"
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
            <div
              className="text-body font-semibold"
              style={{ color: 'var(--color-text-primary)' }}
            >
              Calculate Routes
            </div>
            <p
              className="text-caption mt-1"
              style={{ color: 'var(--color-text-secondary)' }}
            >
              Driving, Cycling, Walking, Transit
            </p>
          </div>
        </label>

        {/* Calculate Button */}
        <button
          onClick={onCalculateRoutes}
          disabled={!routesCalculationEnabled || routesLoading}
          className="w-full brutal-button mb-5"
          style={{
            opacity: !routesCalculationEnabled || routesLoading ? 0.5 : 1,
            cursor: !routesCalculationEnabled || routesLoading ? 'not-allowed' : 'pointer',
          }}
        >
          {routesLoading ? 'CALCULATING...' : 'CALCULATE ROUTES'}
        </button>

        {/* Error Display */}
        {routingError && (
          <div
            className="p-4"
            style={{
              background: '#FFF5F5',
              border: '3px solid var(--color-bright-coral)',
            }}
          >
            <div
              className="text-mono uppercase mb-2"
              style={{
                fontSize: '0.75rem',
                color: 'var(--color-bright-coral)',
                letterSpacing: '0.1em',
                fontWeight: 700,
              }}
            >
              ⚠ ERROR
            </div>
            <div
              className="text-caption"
              style={{ color: 'var(--color-text-primary)' }}
            >
              {routingError}
            </div>
          </div>
        )}

        {/* Success Statistics */}
        {routingStats && !routingError && (
          <div
            className="p-4"
            style={{
              background: routingStats.success_rate > 50 ? '#F0FFF4' : '#FFF5F5',
              border: `3px solid ${
                routingStats.success_rate > 50 ? 'var(--color-mint-green)' : 'var(--color-bright-coral)'
              }`,
            }}
          >
            <div
              className="text-mono uppercase mb-3"
              style={{
                fontSize: '0.75rem',
                color: routingStats.success_rate > 50 ? 'var(--color-mint-green)' : 'var(--color-bright-coral)',
                letterSpacing: '0.1em',
                fontWeight: 700,
              }}
            >
              ✓ COMPLETE
            </div>

            {/* Overall Stats */}
            <div className="grid grid-cols-2 gap-3 mb-4">
              <div>
                <div
                  className="text-caption mb-1"
                  style={{ color: 'var(--color-text-secondary)' }}
                >
                  Success Rate
                </div>
                <div
                  className="text-mono font-bold"
                  style={{
                    fontSize: '1.5rem',
                    color: routingStats.success_rate > 50 ? 'var(--color-mint-green)' : 'var(--color-bright-coral)',
                    lineHeight: '1',
                  }}
                >
                  {routingStats.success_rate}%
                </div>
              </div>
              <div>
                <div
                  className="text-caption mb-1"
                  style={{ color: 'var(--color-text-secondary)' }}
                >
                  Total Routes
                </div>
                <div
                  className="text-mono font-bold"
                  style={{
                    fontSize: '1.5rem',
                    color: 'var(--color-sky-blue)',
                    lineHeight: '1',
                  }}
                >
                  {routingStats.successful}/{routingStats.total_requests}
                </div>
              </div>
            </div>

            {/* Per-Mode Stats */}
            <div
              className="pt-3 space-y-2"
              style={{
                borderTop: '2px solid var(--color-border-light)',
              }}
            >
              <div
                className="text-mono uppercase"
                style={{
                  fontSize: '0.7rem',
                  color: 'var(--color-text-secondary)',
                  letterSpacing: '0.1em',
                  fontWeight: 600,
                }}
              >
                BY MODE
              </div>
              {Object.entries(routingStats.by_mode || {}).map(([mode, stats]: [string, any]) => (
                <div key={mode} className="flex justify-between items-center">
                  <span
                    className="text-caption capitalize"
                    style={{ color: 'var(--color-text-primary)' }}
                  >
                    {mode}
                  </span>
                  <span
                    className="text-mono font-semibold"
                    style={{
                      fontSize: '0.875rem',
                      color: stats.success_rate > 50 ? 'var(--color-mint-green)' : 'var(--color-bright-coral)',
                    }}
                  >
                    {stats.successful}/{stats.successful + stats.failed}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
