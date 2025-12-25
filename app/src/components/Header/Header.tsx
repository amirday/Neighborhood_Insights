'use client';

interface HeaderProps {
  poiCount?: number;
}

export function Header({ poiCount = 0 }: HeaderProps) {
  return (
    <header
      className="fixed top-0 left-0 right-0 bg-white/95 backdrop-blur-sm border-b border-gray-200 shadow-sm"
      style={{
        height: 'var(--header-height)',
        zIndex: 'var(--z-header)',
      }}
    >
      <div className="h-full flex items-center justify-between px-6">
        {/* Left: Title */}
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Neighborhood Insights
          </h1>
          <p className="text-sm text-gray-600">
            Explore Israel&apos;s Points of Interest
          </p>
        </div>

        {/* Right: Live indicator */}
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
          <span>Live Data</span>
          {poiCount > 0 && (
            <span className="ml-2 text-xs bg-gray-100 px-2 py-1 rounded-full">
              {poiCount.toLocaleString()} POIs
            </span>
          )}
        </div>
      </div>
    </header>
  );
}
