// Geographic utility functions

/**
 * Calculate distance between two geographic coordinates using Haversine formula
 * @param lat1 Latitude of first point
 * @param lon1 Longitude of first point
 * @param lat2 Latitude of second point
 * @param lon2 Longitude of second point
 * @returns Distance in kilometers
 */
export const calculateDistance = (
  lat1: number,
  lon1: number,
  lat2: number,
  lon2: number
): number => {
  const R = 6371; // Earth's radius in kilometers
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a =
    Math.sin(dLat/2) * Math.sin(dLat/2) +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
    Math.sin(dLon/2) * Math.sin(dLon/2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
  return R * c;
};

/**
 * Calculate driving time in minutes based on distance and speed
 * @param distanceKm Distance in kilometers
 * @param speedKmh Average speed in km/h
 * @returns Estimated driving time in minutes
 */
export const calculateDrivingTime = (distanceKm: number, speedKmh: number): number => {
  return (distanceKm / speedKmh) * 60; // Convert hours to minutes
};

/**
 * Get Tailwind color class based on distance ratio
 * @param ratio Distance ratio (0-1)
 * @returns Tailwind color class name
 */
export const getDistanceColor = (ratio: number): string => {
  if (ratio < 0.33) return 'emerald-500';  // Green for close distances
  if (ratio < 0.67) return 'amber-500';    // Orange for medium distances
  return 'red-500';                        // Red for far distances
};

/**
 * Check if coordinates are within Israel's bounding box
 * @param lat Latitude
 * @param lon Longitude
 * @returns True if coordinates are in Israel
 */
export const isInIsrael = (lat: number, lon: number): boolean => {
  return lat >= 29.0 && lat <= 33.8 && lon >= 34.2 && lon <= 35.9;
};
