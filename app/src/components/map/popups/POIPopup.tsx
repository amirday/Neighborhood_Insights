'use client';

import { Button } from '@/components/ui/button';
import { POI } from '@/types';

interface Props {
  poi: POI;
}

/**
 * POIPopup Component
 *
 * Displays information about a Point of Interest when clicked on the map.
 */
export function POIPopup({ poi }: Props) {
  const googleMapsUrl = `https://www.google.com/maps/search/?api=1&query=${poi.latitude},${poi.longitude}`;
  const streetViewUrl = `https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=${poi.latitude},${poi.longitude}`;

  // Format POI type for display
  const formattedType = poi.type.replace('_', ' ');
  const typeColors: Record<string, { bg: string; border: string; text: string }> = {
    schools: { bg: '#E0F2FE', border: '#0EA5E9', text: '#0C4A6E' },
    kindergartens: { bg: '#DCFCE7', border: '#10B981', text: '#064E3B' },
    clinics: { bg: '#FEE2E2', border: '#EF4444', text: '#7F1D1D' },
    bus_stops: { bg: '#FEF3C7', border: '#F59E0B', text: '#78350F' },
  };
  const colors = typeColors[poi.type] || { bg: '#F3F4F6', border: '#6B7280', text: '#1F2937' };

  return (
    <div
      className="min-w-[300px] max-w-[420px]"
      style={{
        background: 'var(--color-surface)',
        fontFamily: 'Outfit, sans-serif',
      }}
    >
      {/* Header with diagonal accent */}
      <div
        className="px-5 py-4 relative overflow-hidden"
        style={{
          background: 'var(--color-surface)',
          borderBottom: `3px solid ${colors.border}`,
        }}
      >
        {/* Diagonal stripe */}
        <div
          className="absolute top-0 left-0 h-full w-20 opacity-15"
          style={{
            background: `linear-gradient(135deg, ${colors.border} 0%, transparent 100%)`,
            clipPath: 'polygon(0 0, 100% 0, 70% 100%, 0 100%)',
          }}
        />

        <div className="relative">
          {/* Type badge */}
          <div
            className="inline-block px-4 py-2 mb-2"
            style={{
              background: colors.bg,
              border: `3px solid ${colors.border}`,
              boxShadow: `3px 3px 0 var(--color-border)`,
            }}
          >
            <span
              className="text-mono uppercase font-bold"
              style={{
                fontSize: '0.7rem',
                color: colors.text,
                letterSpacing: '0.05em',
              }}
            >
              {formattedType}
            </span>
          </div>

          {/* POI name */}
          <h3
            className="text-display"
            style={{
              fontSize: '1.5rem',
              color: 'var(--color-text-primary)',
              lineHeight: '1.2',
              marginBottom: '0.25rem',
            }}
          >
            {poi.name_he || poi.name || 'Unnamed Location'}
          </h3>

          {/* English name if available */}
          {poi.name && poi.name_he && poi.name !== poi.name_he && (
            <p
              className="text-body"
              style={{
                color: 'var(--color-text-secondary)',
                fontSize: '0.875rem',
              }}
            >
              {poi.name}
            </p>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="px-5 py-4 space-y-3">
        {/* Address */}
        {poi.address && (
          <div
            className="p-3"
            style={{
              background: '#F8F9FA',
              border: '2px solid var(--color-border-light)',
            }}
          >
            <div
              className="text-mono uppercase mb-1"
              style={{
                fontSize: '0.65rem',
                color: 'var(--color-text-secondary)',
                letterSpacing: '0.05em',
                fontWeight: 700,
              }}
            >
              Address
            </div>
            <div
              className="text-body"
              style={{
                color: 'var(--color-text-primary)',
                fontSize: '0.875rem',
                fontWeight: 600,
              }}
            >
              {poi.address}
            </div>
          </div>
        )}

        {/* Symbol */}
        {poi.symbol && (
          <div
            className="p-3"
            style={{
              background: '#F8F9FA',
              border: '2px solid var(--color-border-light)',
            }}
          >
            <div
              className="text-mono uppercase mb-1"
              style={{
                fontSize: '0.65rem',
                color: 'var(--color-text-secondary)',
                letterSpacing: '0.05em',
                fontWeight: 700,
              }}
            >
              Symbol
            </div>
            <div
              className="text-body"
              style={{
                color: 'var(--color-text-primary)',
                fontSize: '0.875rem',
                fontWeight: 600,
              }}
            >
              {poi.symbol}
            </div>
          </div>
        )}

        {/* Coordinates */}
        <div
          className="p-3"
          style={{
            background: '#F8F9FA',
            border: '2px solid var(--color-border-light)',
          }}
        >
          <div
            className="text-mono uppercase mb-1"
            style={{
              fontSize: '0.65rem',
              color: 'var(--color-text-secondary)',
              letterSpacing: '0.05em',
              fontWeight: 700,
            }}
          >
            Coordinates
          </div>
          <div
            className="text-mono"
            style={{
              color: 'var(--color-text-primary)',
              fontSize: '0.8rem',
              fontWeight: 600,
            }}
          >
            {poi.latitude.toFixed(6)}, {poi.longitude.toFixed(6)}
          </div>
        </div>
      </div>

      {/* Action buttons */}
      <div className="px-5 pb-5 flex gap-3">
        <Button asChild variant="secondary" size="sm" className="flex-1">
          <a href={googleMapsUrl} target="_blank" rel="noopener noreferrer">
            Maps
          </a>
        </Button>
        <Button asChild variant="default" size="sm" className="flex-1">
          <a href={streetViewUrl} target="_blank" rel="noopener noreferrer">
            Street View
          </a>
        </Button>
      </div>
    </div>
  );
}
