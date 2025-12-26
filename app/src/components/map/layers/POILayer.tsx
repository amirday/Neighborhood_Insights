'use client';

import { useEffect } from 'react';
import { createRoot } from 'react-dom/client';
import mapboxgl from 'mapbox-gl';
import { useMapStore } from '@/stores/mapStore';
import { usePOIStore } from '@/stores/poiStore';
import { colors } from '@/design-system/tokens/colors';

/**
 * POILayer Component
 *
 * Manages the Points of Interest layer on the map.
 * This component doesn't render any UI - it only manages map layer effects.
 */
export function POILayer() {
  const map = useMapStore((state) => state.map);
  const mapReady = useMapStore((state) => state.mapReady);
  const pois = usePOIStore((state) => state.pois);
  const selectedTypes = usePOIStore((state) => state.selectedTypes);

  // Add POI source and layer when map is ready and we have POIs
  useEffect(() => {
    if (!map || !mapReady || pois.length === 0) {
      console.log('POILayer: Waiting for map and POIs...', { map: !!map, mapReady, poisCount: pois.length });
      return;
    }

    console.log('POILayer: Setting up POI layer with', pois.length, 'POIs');

    // Create GeoJSON FeatureCollection from POIs
    const featureCollection: GeoJSON.FeatureCollection = {
      type: 'FeatureCollection',
      features: pois.map((poi) => ({
        type: 'Feature',
        geometry: {
          type: 'Point',
          coordinates: [poi.longitude, poi.latitude],
        },
        properties: poi,
      })),
    };

    // Add or update POI source
    if (map.getSource('pois')) {
      // Update existing source
      (map.getSource('pois') as mapboxgl.GeoJSONSource).setData(featureCollection);
      console.log('POILayer: Updated existing POI source');
    } else {
      // Add new source
      map.addSource('pois', {
        type: 'geojson',
        data: featureCollection,
      });

      // Add circle layer for POI visualization
      // Note: We don't specify beforeId, so it will be added on top of existing layers
      map.addLayer({
        id: 'pois-circles',
        type: 'circle',
        source: 'pois',
        paint: {
          // Responsive circle radius based on zoom level
          'circle-radius': [
            'interpolate',
            ['linear'],
            ['zoom'],
            7, 5,   // At zoom 7: 5px radius (10px diameter)
            10, 8,  // At zoom 10: 8px radius (16px diameter)
            14, 12  // At zoom 14: 12px radius (24px diameter for mobile touch)
          ],
          'circle-stroke-width': 2,
          'circle-stroke-color': '#ffffff',
          // Color based on POI type
          'circle-color': [
            'match',
            ['get', 'type'],
            'schools', colors.poi.schools,
            'kindergartens', colors.poi.kindergartens,
            'clinics', colors.poi.clinics,
            'bus_stops', colors.poi.bus_stops,
            colors.neutral[600], // Default gray for unknown types
          ],
        },
      });

      // Ensure POI layer is on top of statistical areas
      // Move it to the top if statistical area layers exist
      if (map.getLayer('statistical-areas-highlight')) {
        try {
          map.moveLayer('pois-circles');
          console.log('POILayer: Moved POI layer to top');
        } catch (e) {
          console.log('POILayer: Could not move layer (might already be on top)');
        }
      }

      console.log('POILayer: Added POI source and layer to map');

      // Store the click handler so we can remove it later if needed
      const poiClickHandler = (e: mapboxgl.MapMouseEvent) => {
        // Query for POI features at click point
        const poiFeatures = map.queryRenderedFeatures(e.point, {
          layers: ['pois-circles']
        });

        // Only handle if there's a POI feature
        if (!poiFeatures || poiFeatures.length === 0) return;

        // Mark that we handled a POI click (prevent statistical area popup)
        (e as any)._poiHandled = true;

        const poi = poiFeatures[0].properties as any;

        // Close any existing popups first
        const existingPopups = document.querySelectorAll('.mapboxgl-popup');
        existingPopups.forEach(popup => popup.remove());

        // Create popup container
        const popupDiv = document.createElement('div');
        const root = createRoot(popupDiv);

        // Import POIPopup dynamically to avoid circular dependencies
        import('@/components/map/popups/POIPopup').then(({ POIPopup }) => {
          root.render(<POIPopup poi={poi} />);
        });

        new mapboxgl.Popup({
          maxWidth: 'none',
          closeButton: true,
          closeOnClick: true,
        })
          .setLngLat(e.lngLat)
          .setDOMContent(popupDiv)
          .addTo(map);
      };

      // Use map-level click handler with higher priority
      map.on('click', poiClickHandler);

      // Add hover effect
      map.on('mouseenter', 'pois-circles', () => {
        map.getCanvas().style.cursor = 'pointer';
      });

      map.on('mouseleave', 'pois-circles', () => {
        map.getCanvas().style.cursor = '';
      });
    }

    // Cleanup function
    return () => {
      // Note: We don't remove the layer/source here because we want to keep it
      // This component will re-run when dependencies change
    };
  }, [map, mapReady, pois]);

  // Update POI visibility filter based on selected types
  useEffect(() => {
    if (!map || !map.getLayer('pois-circles')) {
      console.log('POILayer: Filter effect - waiting for map/layer', { map: !!map, hasLayer: map?.getLayer('pois-circles') });
      return;
    }

    console.log('POILayer: Updating filter for selected types:', selectedTypes);

    if (selectedTypes.length === 0) {
      // Hide all POIs - use a filter that matches nothing
      map.setFilter('pois-circles', ['==', ['get', 'type'], '__NONE__']);
    } else {
      // Show only selected types
      map.setFilter('pois-circles', ['in', ['get', 'type'], ['literal', selectedTypes]]);
    }
  }, [map, selectedTypes]);

  // This component doesn't render any UI
  return null;
}
