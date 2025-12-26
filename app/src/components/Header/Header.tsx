'use client';

interface HeaderProps {
  poiCount?: number;
}

export function Header({ poiCount = 0 }: HeaderProps) {
  return (
    <header
      className="fixed top-0 left-0 right-0 grid-bg overflow-hidden"
      style={{
        height: 'var(--header-height)',
        zIndex: 'var(--z-header)',
        background: 'var(--color-surface)',
        borderBottom: '4px solid var(--color-border)',
      }}
    >
      {/* Diagonal accent stripe */}
      <div
        className="absolute top-0 left-0 h-full w-64 opacity-20"
        style={{
          background: 'linear-gradient(135deg, var(--color-bright-coral) 0%, transparent 100%)',
          clipPath: 'polygon(0 0, 100% 0, 80% 100%, 0 100%)',
        }}
      />

      <div className="relative h-full flex items-center justify-between px-8">
        {/* Left: Title */}
        <div className="flex items-baseline gap-4">
          <h1
            className="text-display"
            style={{
              fontSize: '3.5rem',
              lineHeight: '1',
              color: 'var(--color-text-primary)',
              textShadow: '4px 4px 0 var(--color-sunny-yellow)',
            }}
          >
            NEIGHBORHOOD
            <br />
            <span style={{ color: 'var(--color-bright-coral)' }}>INSIGHTS</span>
          </h1>
        </div>

        {/* Right: Data indicators */}
        <div className="flex items-center gap-6">
          {/* Live indicator */}
          <div
            className="flex items-center gap-3 px-6 py-3"
            style={{
              background: 'var(--color-surface)',
              border: '3px solid var(--color-border)',
            }}
          >
            <div
              className="w-3 h-3 pulse-glow"
              style={{
                background: 'var(--color-mint-green)',
              }}
            />
            <span
              className="text-mono uppercase tracking-wider"
              style={{
                fontSize: '0.875rem',
                color: 'var(--color-text-primary)',
                fontWeight: 600,
              }}
            >
              LIVE DATA
            </span>
          </div>

          {/* POI Count */}
          {poiCount > 0 && (
            <div
              className="px-6 py-3"
              style={{
                background: 'var(--color-bright-coral)',
                border: '3px solid var(--color-border)',
                boxShadow: '4px 4px 0 var(--color-sky-blue)',
              }}
            >
              <div className="flex items-baseline gap-2">
                <span
                  className="text-mono font-bold"
                  style={{
                    fontSize: '1.75rem',
                    color: 'var(--color-surface)',
                    lineHeight: '1',
                  }}
                >
                  {poiCount.toLocaleString()}
                </span>
                <span
                  className="text-mono uppercase"
                  style={{
                    fontSize: '0.75rem',
                    color: 'var(--color-surface)',
                    fontWeight: 700,
                  }}
                >
                  POIs
                </span>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
