'use client';

import { useEffect } from 'react';
import mapboxgl from 'mapbox-gl';
import { useMapStore } from '@/stores/mapStore';
import { useRoutingStore } from '@/stores/routingStore';
import { colors } from '@/design-system/tokens/colors';

/**
 * JobCentersLayer Component
 *
 * Manages the job centers layer on the map.
 */
export function JobCentersLayer() {
  const map = useMapStore((state) => state.map);
  const mapReady = useMapStore((state) => state.mapReady);
  const jobCenters = useRoutingStore((state) => state.jobCenters);
  const selectedJobCenterTypes = useRoutingStore((state) => state.selectedJobCenterTypes);
  const selectedJobCenter = useRoutingStore((state) => state.selectedJobCenter);
  const setSelectedJobCenter = useRoutingStore((state) => state.setSelectedJobCenter);

  useEffect(() => {
    if (!map || !mapReady || jobCenters.length === 0) return;

    // Filter job centers based on selected types
    const filteredJobCenters = jobCenters.filter((center) =>
      selectedJobCenterTypes.includes(center.type)
    );

    console.log('Setting up job centers layer with', filteredJobCenters.length, 'centers (filtered from', jobCenters.length, ')');

    const featureCollection: GeoJSON.FeatureCollection = {
      type: 'FeatureCollection',
      features: filteredJobCenters.map((center) => ({
        type: 'Feature',
        geometry: {
          type: 'Point',
          coordinates: [center.longitude, center.latitude],
        },
        properties: center,
      })),
    };

    if (map.getSource('job-centers')) {
      (map.getSource('job-centers') as mapboxgl.GeoJSONSource).setData(featureCollection);
    } else {
      map.addSource('job-centers', {
        type: 'geojson',
        data: featureCollection,
      });

      map.addLayer({
        id: 'job-centers-circles',
        type: 'circle',
        source: 'job-centers',
        paint: {
          'circle-radius': [
            'interpolate',
            ['linear'],
            ['zoom'],
            7, 6,
            10, 10,
            14, 14
          ],
          'circle-color': colors.map.jobCenters,
          'circle-stroke-width': [
            'case',
            ['==', ['get', 'id'], selectedJobCenter?.id ?? -1],
            4, // Selected job center has thicker stroke
            2  // Default stroke
          ],
          'circle-stroke-color': [
            'case',
            ['==', ['get', 'id'], selectedJobCenter?.id ?? -1],
            '#FBBF24', // Yellow stroke for selected
            '#ffffff'   // White stroke for others
          ],
        },
      });

      // Ensure job centers layer is on top of statistical areas
      if (map.getLayer('statistical-areas-highlight')) {
        try {
          map.moveLayer('job-centers-circles');
          console.log('JobCentersLayer: Moved job centers layer to top');
        } catch (e) {
          console.log('JobCentersLayer: Could not move layer (might already be on top)');
        }
      }

      // Add click handler for job centers using map-level handler
      const jobCenterClickHandler = (e: mapboxgl.MapMouseEvent) => {
        // Query for job center features at click point
        const jobCenterFeatures = map.queryRenderedFeatures(e.point, {
          layers: ['job-centers-circles']
        });

        // Only handle if there's a job center feature
        if (!jobCenterFeatures || jobCenterFeatures.length === 0) return;

        // Mark that we handled a job center click
        (e as any)._poiHandled = true;
        (e as any)._jobCenterHandled = true;

        const feature = jobCenterFeatures[0];
        const props = feature.properties || {};

        // Select this job center for routing calculations
        const jobCenter = jobCenters.find((jc) => jc.id === props.id);
        if (jobCenter) {
          setSelectedJobCenter(jobCenter);
        }

        // Close any existing popups first
        const existingPopups = document.querySelectorAll('.mapboxgl-popup');
        existingPopups.forEach(popup => popup.remove());

        const popupContent = `
          <div style="padding: 12px; min-width: 200px;">
            <h3 style="font-size: 16px; font-weight: bold; margin-bottom: 8px; color: #111827;">
              ${props.name_he || props.name || 'Job Center'}
            </h3>
            ${props.estimated_employees ? `
              <div style="font-size: 14px; color: #6B7280; margin-bottom: 4px;">
                Employees: <strong>${props.estimated_employees.toLocaleString()}</strong>
              </div>
            ` : ''}
            ${props.type ? `
              <div style="font-size: 14px; color: #6B7280; margin-bottom: 4px;">
                Type: <strong>${props.type}</strong>
              </div>
            ` : ''}
            <div style="font-size: 12px; color: #9CA3AF; margin-top: 8px;">
              ${props.latitude.toFixed(6)}, ${props.longitude.toFixed(6)}
            </div>
            <div style="margin-top: 12px; padding-top: 12px; border-top: 1px solid #E5E7EB;">
              <div style="font-size: 12px; color: #059669; font-weight: 600;">
                ✓ Selected for routing analysis
              </div>
            </div>
          </div>
        `;

        new mapboxgl.Popup({
          maxWidth: '300px',
          closeButton: true,
          closeOnClick: true,
        })
          .setLngLat(e.lngLat)
          .setHTML(popupContent)
          .addTo(map);
      };

      map.on('click', jobCenterClickHandler);

      // Hover effect
      map.on('mouseenter', 'job-centers-circles', () => {
        map.getCanvas().style.cursor = 'pointer';
      });

      map.on('mouseleave', 'job-centers-circles', () => {
        map.getCanvas().style.cursor = '';
      });

      console.log('Job centers layer added to map');
    }

    // Update layer styling when selected job center changes
    if (map.getLayer('job-centers-circles')) {
      map.setPaintProperty('job-centers-circles', 'circle-stroke-width', [
        'case',
        ['==', ['get', 'id'], selectedJobCenter?.id ?? -1],
        4,
        2
      ]);
      map.setPaintProperty('job-centers-circles', 'circle-stroke-color', [
        'case',
        ['==', ['get', 'id'], selectedJobCenter?.id ?? -1],
        '#FBBF24',
        '#ffffff'
      ]);
    }
  }, [map, mapReady, jobCenters, selectedJobCenterTypes, selectedJobCenter, setSelectedJobCenter]);

  return null;
}
