// Color utility functions for POI types

/**
 * Get Tailwind background color class for POI type
 * @param type POI type string
 * @returns Tailwind background color class
 */
export const getPOIColorClass = (type: string): string => {
  const colors: Record<string, string> = {
    schools: 'bg-blue-500',
    kindergartens: 'bg-emerald-500',
    clinics: 'bg-red-500',
    bus_stops: 'bg-amber-500',
    job_center: 'bg-red-600',
  };
  return colors[type] || 'bg-gray-500';
};

/**
 * Get Tailwind text color class for POI type
 * @param type POI type string
 * @returns Tailwind text color class
 */
export const getPOITextColorClass = (type: string): string => {
  const colors: Record<string, string> = {
    schools: 'text-blue-500',
    kindergartens: 'text-emerald-500',
    clinics: 'text-red-500',
    bus_stops: 'text-amber-500',
    job_center: 'text-red-600',
  };
  return colors[type] || 'text-gray-500';
};

/**
 * Get RGB color string for Mapbox (from Tailwind color names)
 * @param type POI type string
 * @returns RGB color string
 */
export const getPOIHexColor = (type: string): string => {
  const colors: Record<string, string> = {
    schools: 'rgb(59, 130, 246)',      // blue-500
    kindergartens: 'rgb(16, 185, 129)', // emerald-500
    clinics: 'rgb(239, 68, 68)',       // red-500
    bus_stops: 'rgb(245, 158, 11)',    // amber-500
    job_center: 'rgb(220, 38, 38)',    // red-600
  };
  return colors[type] || 'rgb(107, 114, 128)'; // gray-500
};
