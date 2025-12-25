'use client';

import { useEffect, useState } from 'react';

interface ResponsiveDimensions {
  isMobile: boolean;
  isTablet: boolean;
  isDesktop: boolean;
  width: number;
  height: number;
}

/**
 * Hook to track responsive breakpoints and viewport dimensions
 * Breakpoints: mobile (<768px), tablet (768-1024px), desktop (≥1024px)
 */
export function useResponsive(): ResponsiveDimensions {
  const [dimensions, setDimensions] = useState<ResponsiveDimensions>({
    isMobile: false,
    isTablet: false,
    isDesktop: false,
    width: 0,
    height: 0,
  });

  useEffect(() => {
    const updateDimensions = () => {
      const width = window.innerWidth;
      const height = window.innerHeight;

      setDimensions({
        isMobile: width < 768,
        isTablet: width >= 768 && width < 1024,
        isDesktop: width >= 1024,
        width,
        height,
      });
    };

    updateDimensions();
    window.addEventListener('resize', updateDimensions);
    return () => window.removeEventListener('resize', updateDimensions);
  }, []);

  return dimensions;
}
