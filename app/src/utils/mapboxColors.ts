// Mapbox color utilities - Convert Tailwind color names to RGB for Mapbox

/**
 * Mapping of Tailwind color class names to RGB values for use in Mapbox
 * Mapbox requires RGB/hex colors, not class names
 */
export const tailwindToRGB = {
  'blue-500': 'rgb(59, 130, 246)',
  'blue-600': 'rgb(37, 99, 235)',
  'blue-700': 'rgb(29, 78, 216)',
  'emerald-500': 'rgb(16, 185, 129)',
  'emerald-600': 'rgb(5, 150, 105)',
  'red-500': 'rgb(239, 68, 68)',
  'red-600': 'rgb(220, 38, 38)',
  'amber-500': 'rgb(245, 158, 11)',
  'amber-600': 'rgb(217, 119, 6)',
  'violet-500': 'rgb(139, 92, 246)',
  'gray-500': 'rgb(107, 114, 128)',
} as const;

/**
 * Get Mapbox-compatible RGB color from Tailwind class name
 * @param tailwindClass Tailwind color class name (e.g., 'blue-500')
 * @returns RGB color string (e.g., 'rgb(59, 130, 246)')
 */
export const getMapboxColor = (tailwindClass: keyof typeof tailwindToRGB): string => {
  return tailwindToRGB[tailwindClass] || tailwindToRGB['gray-500'];
};
