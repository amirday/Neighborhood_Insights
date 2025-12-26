'use client';

import { useEffect, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import mapboxgl from 'mapbox-gl';
import { useMapStore } from '@/stores/mapStore';
import { useRoutingStore } from '@/stores/routingStore';
import { StatisticalAreaPopup } from '@/components/map/popups/StatisticalAreaPopup';
import { calculateDistance, calculateDrivingTime } from '@/utils/geo';

/**
 * StatisticalAreasLayer Component
 *
 * Manages the statistical areas layer on the map with distance-based coloring.
 */
export function StatisticalAreasLayer() {
  const map = useMapStore((state) => state.map);
  const mapReady = useMapStore((state) => state.mapReady);
  const selectedJobCenter = useRoutingStore((state) => state.selectedJobCenter);
  const distanceCalculationEnabled = useRoutingStore((state) => state.distanceCalculationEnabled);
  const averageDrivingSpeed = useRoutingStore((state) => state.averageDrivingSpeed);
  const drivingTimeThreshold = useRoutingStore((state) => state.drivingTimeThreshold);

  const [showLayer, setShowLayer] = useState(true);
  const [loading, setLoading] = useState(false);
  const geojsonDataRef = useRef<any>(null);

  // Load statistical areas
  useEffect(() => {
    if (!map || !mapReady || !showLayer) return;

    const loadStatisticalAreas = async () => {
      setLoading(true);
      try {
        console.log('Loading statistical areas...');
        const response = await fetch('http://localhost:8000/statistical-areas/geojson');
        const geojsonData = await response.json();
        console.log('Loaded statistical areas:', geojsonData.features.length);

        geojsonDataRef.current = geojsonData;

        // Add source if it doesn't exist
        if (!map.getSource('statistical-areas')) {
          map.addSource('statistical-areas', {
            type: 'geojson',
            data: geojsonData,
          });

          // Add fill layer
          map.addLayer({
            id: 'statistical-areas-fill',
            type: 'fill',
            source: 'statistical-areas',
            paint: {
              'fill-color': '#3B82F6',
              'fill-opacity': 0.3,
            },
          });

          // Add boundary layer
          map.addLayer({
            id: 'statistical-areas-boundaries',
            type: 'line',
            source: 'statistical-areas',
            paint: {
              'line-color': '#2563EB',
              'line-width': 1.5,
              'line-opacity': 0.7,
            },
          });

          // Add highlight layer for hover
          map.addLayer({
            id: 'statistical-areas-highlight',
            type: 'fill',
            source: 'statistical-areas',
            paint: {
              'fill-color': '#3B82F6',
              'fill-opacity': 0.5,
            },
            filter: ['==', 'OBJECTID', ''],
          });

          // Add click handler with delay to allow POI/JobCenter handlers to run first
          map.on('click', (e) => {
            // Use setTimeout to let POI/JobCenter handlers run first
            setTimeout(() => {
              // Check if POI or JobCenter already handled this click
              if ((e as any)._poiHandled || (e as any)._jobCenterHandled) {
                return;
              }

              // Check if there are any POI features at this point (higher priority)
              const poiFeatures = map.queryRenderedFeatures(e.point, {
                layers: ['pois-circles']
              });

              // Check if there are any job center features at this point (higher priority)
              const jobCenterFeatures = map.queryRenderedFeatures(e.point, {
                layers: ['job-centers-circles']
              });

              // If there's a POI or job center at this location, don't show the statistical area popup
              if ((poiFeatures && poiFeatures.length > 0) || (jobCenterFeatures && jobCenterFeatures.length > 0)) {
                return;
              }

              // Query for statistical area features
              const statFeatures = map.queryRenderedFeatures(e.point, {
                layers: ['statistical-areas-fill']
              });

              if (!statFeatures || statFeatures.length === 0) return;

              const feature = statFeatures[0];
              const properties = feature.properties || {};

              // Close any existing popups first
              const existingPopups = document.querySelectorAll('.mapboxgl-popup');
              existingPopups.forEach(popup => popup.remove());

              // Create popup container
              const popupDiv = document.createElement('div');
              const root = createRoot(popupDiv);
              root.render(
                <StatisticalAreaPopup
                  properties={properties}
                  coordinates={{ lat: e.lngLat.lat, lng: e.lngLat.lng }}
                />
              );

              new mapboxgl.Popup({
                maxWidth: 'none',
                closeButton: true,
                closeOnClick: true,
              })
                .setLngLat(e.lngLat)
                .setDOMContent(popupDiv)
                .addTo(map);
            }, 0);
          });

          // Add hover effects
          let hoveredId: string | number | null = null;

          map.on('mouseenter', 'statistical-areas-fill', (e) => {
            map.getCanvas().style.cursor = 'pointer';
            if (e.features && e.features.length > 0) {
              hoveredId = e.features[0].properties?.OBJECTID;
              if (hoveredId) {
                map.setFilter('statistical-areas-highlight', ['==', 'OBJECTID', hoveredId]);
              }
            }
          });

          map.on('mouseleave', 'statistical-areas-fill', () => {
            map.getCanvas().style.cursor = '';
            map.setFilter('statistical-areas-highlight', ['==', 'OBJECTID', '']);
            hoveredId = null;
          });
        }
      } catch (error) {
        console.error('Error loading statistical areas:', error);
      } finally {
        setLoading(false);
      }
    };

    loadStatisticalAreas();
  }, [map, mapReady, showLayer]);

  // Apply distance-based coloring
  useEffect(() => {
    if (!map || !geojsonDataRef.current || !selectedJobCenter || !distanceCalculationEnabled) {
      // Reset to default coloring
      if (map?.getLayer('statistical-areas-fill')) {
        map.setPaintProperty('statistical-areas-fill', 'fill-color', '#3B82F6');
        map.setPaintProperty('statistical-areas-fill', 'fill-opacity', 0.3);
      }
      return;
    }

    const geojsonData = geojsonDataRef.current;
    const allDistances: number[] = [];

    // Calculate distances for each feature
    geojsonData.features.forEach((feature: any) => {
      if (feature.geometry.type === 'Polygon' || feature.geometry.type === 'MultiPolygon') {
        const coordinates = feature.geometry.type === 'Polygon'
          ? feature.geometry.coordinates[0]
          : feature.geometry.coordinates[0][0];

        let sumLat = 0, sumLng = 0, pointCount = 0;
        coordinates.forEach((coord: number[]) => {
          if (coord && coord.length >= 2) {
            sumLng += coord[0];
            sumLat += coord[1];
            pointCount++;
          }
        });

        if (pointCount > 0) {
          const centerLat = sumLat / pointCount;
          const centerLng = sumLng / pointCount;
          const distance = calculateDistance(
            selectedJobCenter.latitude,
            selectedJobCenter.longitude,
            centerLat,
            centerLng
          );

          if (!isNaN(distance) && isFinite(distance)) {
            const drivingTime = calculateDrivingTime(distance, averageDrivingSpeed);
            feature.properties.distance_km = Math.round(distance * 100) / 100;
            feature.properties.driving_time_minutes = Math.round(drivingTime * 10) / 10;
            feature.properties.is_within_threshold = drivingTime <= drivingTimeThreshold;
            allDistances.push(distance);
          }
        }
      }
    });

    const maxDistance = allDistances.length > 0 ? Math.max(...allDistances) : 1;
    geojsonData.features.forEach((feature: any) => {
      if (feature.properties.distance_km !== null) {
        feature.properties.distance_ratio = feature.properties.distance_km / maxDistance;
      }
    });

    // Update source
    (map.getSource('statistical-areas') as mapboxgl.GeoJSONSource)?.setData(geojsonData);

    // Apply distance-based coloring
    map.setPaintProperty('statistical-areas-fill', 'fill-color', [
      'case',
      ['all', ['has', 'distance_ratio'], ['!=', ['get', 'distance_ratio'], null], ['get', 'is_within_threshold']],
      [
        'case',
        ['<', ['number', ['get', 'distance_ratio']], 0.33],
        ['rgba', 16, 185, 129, 1],
        ['<', ['number', ['get', 'distance_ratio']], 0.67],
        ['rgba', 245, 158, 11, 1],
        ['rgba', 239, 68, 68, 1]
      ],
      ['rgba', 0, 0, 0, 0]
    ]);

    map.setPaintProperty('statistical-areas-fill', 'fill-opacity', [
      'case',
      ['all', ['has', 'is_within_threshold'], ['get', 'is_within_threshold']],
      0.3,
      0
    ]);

    console.log('Applied distance coloring');
  }, [map, selectedJobCenter, distanceCalculationEnabled, averageDrivingSpeed, drivingTimeThreshold]);

  return null;
}
