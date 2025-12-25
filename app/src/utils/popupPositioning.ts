import mapboxgl from 'mapbox-gl';

/**
 * Smart popup positioning to prevent cutoff at screen edges
 * Automatically selects best anchor point based on click location
 */
export const getSmartPopupConfig = (
  map: mapboxgl.Map,
  clickPoint: { x: number; y: number }
): mapboxgl.PopupOptions => {
  const canvas = map.getCanvas();
  const { clientWidth, clientHeight } = canvas;

  // Determine best anchor based on click position
  const clickX = clickPoint.x;
  const clickY = clickPoint.y;

  // Calculate which area of the screen was clicked
  const isBottom = clickY > clientHeight * 0.6;  // Bottom 40% of screen
  const isTop = clickY < clientHeight * 0.4;     // Top 40% of screen
  const isRight = clickX > clientWidth * 0.6;    // Right 40% of screen
  const isLeft = clickX < clientWidth * 0.4;     // Left 40% of screen

  // Smart anchor selection to prevent cutoff
  let anchor: 'top' | 'bottom' | 'left' | 'right' | 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right' | 'center';

  // Corner cases first
  if (isBottom && isRight) {
    anchor = 'bottom-right';
  } else if (isBottom && isLeft) {
    anchor = 'bottom-left';
  } else if (isTop && isRight) {
    anchor = 'top-right';
  } else if (isTop && isLeft) {
    anchor = 'top-left';
  }
  // Edge cases
  else if (isBottom) {
    anchor = 'bottom';
  } else if (isTop) {
    anchor = 'top';
  } else if (isRight) {
    anchor = 'right';
  } else if (isLeft) {
    anchor = 'left';
  }
  // Center of screen - default to top
  else {
    anchor = 'top';
  }

  return {
    closeButton: true,
    anchor,
    offset: 15,
    maxWidth: 'min(500px, 92vw)',
    className: 'smart-popup', // for additional styling if needed
  };
};
