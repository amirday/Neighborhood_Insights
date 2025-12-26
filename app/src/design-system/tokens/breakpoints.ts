/**
 * Design System - Breakpoint Tokens
 *
 * Responsive breakpoints for the Neighborhood Insights application.
 * Mobile-first approach.
 */

export const breakpoints = {
  xs: '375px',   // Small phones (iPhone SE)
  sm: '640px',   // Large phones
  md: '768px',   // Tablets (mobile/desktop boundary)
  lg: '1024px',  // Desktop
  xl: '1280px',  // Large desktop
  '2xl': '1536px', // Extra large screens
};

/**
 * Breakpoint values in pixels (for JavaScript calculations)
 */
export const breakpointsPx = {
  xs: 375,
  sm: 640,
  md: 768,
  lg: 1024,
  xl: 1280,
  '2xl': 1536,
};

/**
 * Media query helpers
 */
export const mediaQueries = {
  xs: `@media (min-width: ${breakpoints.xs})`,
  sm: `@media (min-width: ${breakpoints.sm})`,
  md: `@media (min-width: ${breakpoints.md})`,
  lg: `@media (min-width: ${breakpoints.lg})`,
  xl: `@media (min-width: ${breakpoints.xl})`,
  '2xl': `@media (min-width: ${breakpoints['2xl']})`,
};

/**
 * Device type detection helpers
 */
export const deviceTypes = {
  mobile: `(max-width: ${breakpoints.md})`,     // < 768px
  tablet: `(min-width: ${breakpoints.md}) and (max-width: ${breakpoints.lg})`, // 768-1024px
  desktop: `(min-width: ${breakpoints.lg})`,    // >= 1024px
};
