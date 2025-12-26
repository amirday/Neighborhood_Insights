/**
 * Design System - Color Tokens
 *
 * Color palette for the Neighborhood Insights application.
 * Optimized for WCAG 2.1 AA accessibility standards.
 */

export const colors = {
  // Primary - Blue (existing brand color)
  primary: {
    50: '#EFF6FF',
    100: '#DBEAFE',
    200: '#BFDBFE',
    300: '#93C5FD',
    400: '#60A5FA',
    500: '#3B82F6',  // Main brand blue
    600: '#2563EB',
    700: '#1D4ED8',
    800: '#1E40AF',
    900: '#1E3A8A',
  },

  // Success - Green
  success: {
    50: '#F0FDF4',
    100: '#DCFCE7',
    200: '#BBF7D0',
    300: '#86EFAC',
    400: '#4ADE80',
    500: '#10B981',  // Main success green
    600: '#059669',
    700: '#047857',
    800: '#065F46',
    900: '#064E3B',
  },

  // Error - Red
  error: {
    50: '#FEF2F2',
    100: '#FEE2E2',
    200: '#FECACA',
    300: '#FCA5A5',
    400: '#F87171',
    500: '#DC2626',  // Main error red
    600: '#B91C1C',
    700: '#991B1B',
    800: '#7F1D1D',
    900: '#7C1F1F',
  },

  // Warning - Amber
  warning: {
    50: '#FFFBEB',
    100: '#FEF3C7',
    200: '#FDE68A',
    300: '#FCD34D',
    400: '#FBBF24',
    500: '#F59E0B',  // Main warning amber
    600: '#D97706',
    700: '#B45309',
    800: '#92400E',
    900: '#78350F',
  },

  // Info - Sky
  info: {
    50: '#F0F9FF',
    100: '#E0F2FE',
    200: '#BAE6FD',
    300: '#7DD3FC',
    400: '#38BDF8',
    500: '#0EA5E9',
    600: '#0284C7',
    700: '#0369A1',
    800: '#075985',
    900: '#0C4A6E',
  },

  // Transit - Violet (for public transit routes)
  transit: {
    50: '#F5F3FF',
    100: '#EDE9FE',
    200: '#DDD6FE',
    300: '#C4B5FD',
    400: '#A78BFA',
    500: '#8B5CF6',
    600: '#7C3AED',
    700: '#6D28D9',
    800: '#5B21B6',
    900: '#4C1D95',
  },

  // Neutral - Gray scale
  neutral: {
    0: '#FFFFFF',
    50: '#F9FAFB',
    100: '#F3F4F6',
    200: '#E5E7EB',
    300: '#D1D5DB',
    400: '#9CA3AF',
    500: '#6B7280',
    600: '#4B5563',
    700: '#374151',
    800: '#1F2937',
    900: '#111827',
    950: '#030712',
  },

  // POI Type Colors (for map markers)
  poi: {
    schools: '#3B82F6',        // Blue
    kindergartens: '#10B981',  // Green
    clinics: '#DC2626',        // Red
    bus_stops: '#F59E0B',      // Amber
  },

  // Map Colors
  map: {
    jobCenters: '#DC2626',           // Red for job centers
    areaFill: 'rgba(59, 130, 246, 0.1)',  // Light blue with transparency
    areaBorder: '#3B82F6',           // Blue border
    areaHover: 'rgba(59, 130, 246, 0.3)', // Darker blue on hover
    routePreview: '#10B981',         // Green for route lines
  },

  // Distance Color Scale (for distance-based coloring)
  distance: {
    near: '#10B981',    // Green: 0-33% of threshold
    medium: '#F59E0B',  // Orange: 33-67% of threshold
    far: '#DC2626',     // Red: 67-100%+ of threshold
  },
};

/**
 * Get POI color by type
 */
export function getPOIColor(type: string): string {
  return colors.poi[type as keyof typeof colors.poi] || colors.neutral[600];
}

/**
 * Get distance-based color
 * @param ratio - Distance ratio (0-1, where 0 is nearest, 1 is at threshold)
 */
export function getDistanceColor(ratio: number): string {
  if (ratio < 0.33) return colors.distance.near;
  if (ratio < 0.67) return colors.distance.medium;
  return colors.distance.far;
}
