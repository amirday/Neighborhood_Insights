'use client';

import { useEffect, useRef, useState } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';

interface POI {
  id: number;
  name_he: string;
  name_en: string;
  type: string;
  longitude: number;
  latitude: number;
}

interface JobCenter {
  id: number;
  name_he: string;
  name_en: string;
  address: string;
  estimated_employees: number;
  type: string;
  longitude: number;
  latitude: number;
}


export default function Home() {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);
  const [pois, setPois] = useState<POI[]>([]);
  const [poiTypes, setPOITypes] = useState<string[]>([]);
  const [selectedTypes, setSelectedTypes] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [mapReady, setMapReady] = useState(false);
  const [showStatisticalAreas, setShowStatisticalAreas] = useState(true);
  const [statisticalAreasLoading, setStatisticalAreasLoading] = useState(false);
  const [jobCenters, setJobCenters] = useState<JobCenter[]>([]);
  const [showJobCenters, setShowJobCenters] = useState(false);
  const [jobCentersLoading, setJobCentersLoading] = useState(false);
  const [selectedJobCenter, setSelectedJobCenter] = useState<JobCenter | null>(null);
  const [distanceCalculationEnabled, setDistanceCalculationEnabled] = useState(false);
  const [averageDrivingSpeed, setAverageDrivingSpeed] = useState(40); // km/h
  const [drivingTimeThreshold, setDrivingTimeThreshold] = useState(30); // minutes


  // Distance calculation function
  const calculateDistance = (lat1: number, lon1: number, lat2: number, lon2: number): number => {
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

  // Calculate driving time in minutes
  const calculateDrivingTime = (distanceKm: number, speedKmh: number): number => {
    return (distanceKm / speedKmh) * 60; // Convert hours to minutes
  };

  // Get color based on distance
  const getDistanceColor = (distance: number, maxDistance: number): string => {
    const ratio = distance / maxDistance;
    if (ratio < 0.33) return '#10B981'; // Green for short distances
    if (ratio < 0.67) return '#F59E0B'; // Orange for medium distances
    return '#EF4444'; // Red for long distances
  };

  // Fetch POI data from backend only when map is ready
  useEffect(() => {
    if (!mapReady) {
      console.log('Map not ready yet, waiting...');
      return;
    }

    const fetchPOIs = async () => {
      try {
        console.log('Map is ready, fetching POIs...');
        const response = await fetch('/api/pois');
        const data = await response.json();
        console.log('Raw API response:', data);
        console.log('POIs array:', data.pois);
        console.log('POIs array length:', data.pois?.length || 0);
        
        if (!data.pois || !Array.isArray(data.pois)) {
          console.error('No POIs data received from API');
          setLoading(false);
          return;
        }
        
        console.log('First POI:', data.pois[0]);
        
        // Coerce to numbers and hard-filter to Israel bounding box
        const cleaned: POI[] = data.pois
          .map((p: any) => ({
            ...p,
            longitude: Number(p.longitude),
            latitude: Number(p.latitude),
          }))
          .filter((p: POI) => {
            const valid = p.latitude >= 29.0 && p.latitude <= 33.8 &&
                         p.longitude >= 34.2 && p.longitude <= 35.9;
            if (!valid) {
              console.log('Filtered out POI:', p);
            }
            return valid;
          });
        
        console.log('Fetched POIs:', data.pois?.length || 0);
        console.log('Cleaned POIs:', cleaned.length);
        console.log('Sample cleaned POI:', cleaned[0]);
        
        setPois(cleaned);
        const types = Array.from(new Set(cleaned.map((p: POI) => p.type)));
        setPOITypes(types);
        setSelectedTypes(types); // Show all types by default
        setLoading(false);
      } catch (error) {
        console.error('Error fetching POIs:', error);
        setLoading(false);
      }
    };

    fetchPOIs();
  }, [mapReady]);

  // Fetch job centers data when map is ready
  useEffect(() => {
    if (!mapReady) return;

    const fetchJobCenters = async () => {
      try {
        console.log('Fetching job centers...');
        const response = await fetch('http://localhost:8001/job-centers');
        const data = await response.json();
        console.log('Job centers data:', data);

        if (!data.job_centers || !Array.isArray(data.job_centers)) {
          console.error('No job centers data received from API');
          return;
        }

        setJobCenters(data.job_centers);
        console.log('Loaded job centers:', data.job_centers.length);
      } catch (error) {
        console.error('Error fetching job centers:', error);
      }
    };

    fetchJobCenters();
  }, [mapReady]);

  // Handle statistical areas toggle
  useEffect(() => {
    if (!map.current || !mapReady) return;
    const currentMap = map.current;

    const loadStatisticalAreas = async () => {
      if (showStatisticalAreas) {
        setStatisticalAreasLoading(true);
        try {
          console.log('Loading statistical areas...');
          const response = await fetch('http://localhost:8001/statistical-areas/geojson');
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
          const geojsonData = await response.json();
          console.log('Statistical areas loaded:', geojsonData.features.length, 'features');

          // Add source if it doesn't exist
          if (!currentMap.getSource('statistical-areas')) {
            console.log('Adding statistical areas source and layers...');
            currentMap.addSource('statistical-areas', {
              type: 'geojson',
              data: geojsonData
            });

            // Add boundary layer (lines)
            currentMap.addLayer({
              id: 'statistical-areas-boundaries',
              type: 'line',
              source: 'statistical-areas',
              paint: {
                'line-color': '#2563EB',
                'line-width': 1.5,
                'line-opacity': 0.7
              }
            });

            // Add fill layer (areas) with default blue coloring initially
            const fillPaint = {
              'fill-color': '#3B82F6',
              'fill-opacity': 0.3
            };

            currentMap.addLayer({
              id: 'statistical-areas-fill',
              type: 'fill',
              source: 'statistical-areas',
              paint: fillPaint
            }, 'statistical-areas-boundaries'); // Add below boundary layer

            // Add a highlighted fill layer for hover effects
            currentMap.addLayer({
              id: 'statistical-areas-highlight',
              type: 'fill',
              source: 'statistical-areas',
              paint: {
                'fill-color': '#3B82F6',
                'fill-opacity': 0.3
              },
              filter: ['==', 'OBJECTID', ''] // Initially hide all features
            }, 'statistical-areas-boundaries');

            // Add click handler for statistical areas
            currentMap.on('click', 'statistical-areas-fill', (e) => {
              const f = e.features && e.features[0];
              if (!f) return;

              const props: any = f.properties || {};
              const coord = e.lngLat;

              // Define display order and Hebrew names
              const hebrewFieldMap = [
                { key: 'distance_km', name: 'מרחק ממוקד התעסוקה', priority: 0, suffix: ' ק"מ' },
                { key: 'driving_time_minutes', name: 'זמן נסיעה משוער', priority: 1, suffix: ' דקות' },
                { key: 'שם_יישוב', name: 'שם יישוב', priority: 1 },
                { key: 'שם_יישוב_אנגלית', name: 'שם יישוב באנגלית', priority: 2 },
                { key: 'סוג_יישוב', name: 'סוג יישוב', priority: 3 },
                { key: 'אזור_גיאוגרפי', name: 'אזור גיאוגרפי', priority: 4 },
                { key: 'סמל_יישוב', name: 'סמל יישוב', priority: 5 },
                { key: 'שטח_קמ_ר', name: 'שטח', priority: 6, suffix: ' קמ"ר' },
                { key: 'היקף_קמ', name: 'היקף', priority: 7, suffix: ' ק"מ' },
                { key: 'סטטוס_יישוב', name: 'סטטוס יישוב', priority: 8 },
                { key: 'קוד_תפקוד_עיקרי', name: 'קוד תפקוד עיקרי', priority: 9 },
                { key: 'רובע', name: 'רובע', priority: 10 },
                { key: 'תת_רובע', name: 'תת רובע', priority: 11 },
                { key: 'סטטיסטיקה_2022', name: 'קוד סטטיסטיקה 2022', priority: 12 }
              ];

              // Format properties for display
              const displayProps = hebrewFieldMap
                .map(field => {
                  const value = props[field.key];
                  if (value === null || value === undefined || value === '' ||
                      (typeof value === 'number' && isNaN(value))) {
                    return null;
                  }

                  let displayValue = value;

                  // Format numbers
                  if (typeof value === 'number') {
                    if (field.suffix) {
                      displayValue = `${value.toLocaleString()}${field.suffix}`;
                    } else {
                      displayValue = value.toLocaleString();
                    }
                  }

                  return {
                    name: field.name,
                    value: displayValue,
                    priority: field.priority
                  };
                })
                .filter(item => item !== null)
                .sort((a, b) => (a?.priority || 0) - (b?.priority || 0));

              // Get main title
              const mainTitle = props['שם_יישוב'] || props['SHEM_YISHU'] || props['SHEM_YIS_1'] || 'אזור סטטיסטי';

              // Get distance and driving time information if available
              const distanceInfo = props['distance_km'] ? `
                <div style="background:linear-gradient(135deg,#F59E0B,#D97706);color:white;padding:12px;border-radius:12px;margin:16px 0;text-align:center;box-shadow:0 4px 12px rgba(245,158,11,0.3)">
                  <div style="font-size:14px;font-weight:600;margin-bottom:4px">מרחק ממוקד התעסוקה הנבחר</div>
                  <div style="font-size:24px;font-weight:800">${props['distance_km']} ק"מ</div>
                  ${props['driving_time_minutes'] ? `<div style="font-size:18px;font-weight:600;margin-top:6px;color:#FEF3C7">${props['driving_time_minutes']} דקות נסיעה</div>` : ''}
                  ${props['distance_ratio'] ? `<div style="font-size:12px;opacity:0.9;margin-top:2px">יחס: ${(props['distance_ratio'] * 100).toFixed(1)}%</div>` : ''}
                </div>` : '';

              // Create popup content
              const popupContent = `
                <div dir="rtl" style="font-family:Arial,sans-serif;min-width:420px;max-width:500px;direction:rtl;padding:4px">
                  <div style="display:flex;align-items:center;margin-bottom:16px;justify-content:space-between">
                    <span style="font-size:13px;color:#0369A1;background:#E0F2FE;padding:6px 12px;border-radius:16px;font-weight:700">אזור סטטיסטי</span>
                    ${props['אזור_גיאוגרפי'] ? `<span style="font-size:13px;color:#059669;background:#ECFDF5;padding:6px 12px;border-radius:16px;font-weight:700">${props['אזור_גיאוגרפי']}</span>` : ''}
                  </div>

                  <div style="font-size:22px;font-weight:800;color:#111827;line-height:1.2;margin-bottom:8px;text-align:right">
                    ${mainTitle}
                  </div>
                  ${props['שם_יישוב_אנגלית'] ? `<div style="font-size:16px;color:#6B7280;margin-bottom:12px;text-align:right;font-weight:600">${props['שם_יישוב_אנגלית']}</div>` : ''}

                  ${distanceInfo}

                  <div style="margin-bottom:20px;background:#F9FAFB;padding:12px;border-radius:12px">
                    ${displayProps.map(item => `
                      <div style="display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid #E5E7EB;last-child:border-bottom:none">
                        <span style="font-size:15px;color:#374151;font-weight:700;text-align:right">${item.name}</span>
                        <span style="font-size:15px;color:#111827;font-weight:800;text-align:left;margin-right:16px;background:white;padding:4px 8px;border-radius:6px">${item.value}</span>
                      </div>
                    `).join('')}
                  </div>

                  <div style="display:flex;gap:12px;margin-top:20px">
                    <a href="https://www.google.com/maps?q=${coord.lat},${coord.lng}" target="_blank" rel="noopener noreferrer"
                       style="display:inline-block;font-size:14px;background:#2563EB;color:white;padding:12px 16px;border-radius:10px;text-decoration:none;flex:1;text-align:center;font-weight:700;transition:all 0.2s;box-shadow:0 2px 4px rgba(37,99,235,0.2)">מפות גוגל</a>
                    <a href="https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=${coord.lat},${coord.lng}" target="_blank" rel="noopener noreferrer"
                       style="display:inline-block;font-size:14px;background:#059669;color:white;padding:12px 16px;border-radius:10px;text-decoration:none;flex:1;text-align:center;font-weight:700;transition:all 0.2s;box-shadow:0 2px 4px rgba(5,150,105,0.2)">תצוגת רחוב</a>
                  </div>
                </div>
              `;

              new mapboxgl.Popup({ closeButton: true, offset: 15, maxWidth: '500px' })
                .setLngLat(coord)
                .setHTML(popupContent)
                .addTo(currentMap);
            });

            // Add hover effects for statistical areas
            let hoveredAreaId: string | number | null = null;

            currentMap.on('mouseenter', 'statistical-areas-fill', (e) => {
              currentMap.getCanvas().style.cursor = 'pointer';

              if (e.features && e.features.length > 0) {
                const feature = e.features[0];
                hoveredAreaId = feature.properties?.OBJECTID;

                // Highlight only the hovered area
                if (hoveredAreaId) {
                  currentMap.setFilter('statistical-areas-highlight', ['==', 'OBJECTID', hoveredAreaId]);
                }
              }
            });

            currentMap.on('mouseleave', 'statistical-areas-fill', () => {
              currentMap.getCanvas().style.cursor = '';

              // Remove highlight
              currentMap.setFilter('statistical-areas-highlight', ['==', 'OBJECTID', '']);
              hoveredAreaId = null;
            });

            // Handle mouse move for precise highlighting
            currentMap.on('mousemove', 'statistical-areas-fill', (e) => {
              if (e.features && e.features.length > 0) {
                const feature = e.features[0];
                const newHoveredId = feature.properties?.OBJECTID;

                if (newHoveredId !== hoveredAreaId) {
                  hoveredAreaId = newHoveredId;
                  if (hoveredAreaId) {
                    currentMap.setFilter('statistical-areas-highlight', ['==', 'OBJECTID', hoveredAreaId]);
                  }
                }
              }
            });

            console.log('Added statistical areas layers to map');
          } else {
            // Update existing source
            (currentMap.getSource('statistical-areas') as mapboxgl.GeoJSONSource).setData(geojsonData);
          }

          // Apply distance-based coloring if a job center is selected
          if (selectedJobCenter && distanceCalculationEnabled) {
            console.log('Applying distance calculation from', selectedJobCenter.name_he);

            // Calculate distances and store directly on features
            const allDistances: number[] = [];

            // Single pass: calculate distances and store on each feature
            geojsonData.features.forEach((feature: any) => {
              if (feature.geometry.type === 'Polygon' || feature.geometry.type === 'MultiPolygon') {
                // Get the main polygon coordinates
                const coordinates = feature.geometry.type === 'Polygon'
                  ? feature.geometry.coordinates[0]
                  : feature.geometry.coordinates[0][0]; // First polygon of MultiPolygon

                // Calculate proper centroid using coordinate averaging
                let sumLat = 0, sumLng = 0, pointCount = 0;

                coordinates.forEach((coord: number[]) => {
                  if (coord && coord.length >= 2 && !isNaN(coord[0]) && !isNaN(coord[1])) {
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
                    feature.properties.distance_km = Math.round(distance * 100) / 100; // Round to 2 decimal places
                    feature.properties.driving_time_minutes = Math.round(drivingTime * 10) / 10; // Round to 1 decimal place
                    feature.properties.is_within_threshold = drivingTime <= drivingTimeThreshold;
                    allDistances.push(distance);
                  } else {
                    feature.properties.distance_km = null;
                    feature.properties.driving_time_minutes = null;
                    feature.properties.is_within_threshold = false;
                  }
                } else {
                  feature.properties.distance_km = null;
                  feature.properties.driving_time_minutes = null;
                  feature.properties.is_within_threshold = false;
                }
              } else {
                feature.properties.distance_km = null;
                feature.properties.driving_time_minutes = null;
                feature.properties.is_within_threshold = false;
              }
            });

            // Find max distance and calculate ratios
            const maxDistance = allDistances.length > 0 ? Math.max(...allDistances) : 1;

            // Add distance ratios
            geojsonData.features.forEach((feature: any) => {
              if (feature.properties.distance_km !== null) {
                feature.properties.distance_ratio = feature.properties.distance_km / maxDistance;
              } else {
                feature.properties.distance_ratio = null;
              }
            });

            console.log(`Processed ${allDistances.length} features with distances. Max distance: ${maxDistance.toFixed(2)}km`);

            // Update the source with distance data
            (currentMap.getSource('statistical-areas') as mapboxgl.GeoJSONSource).setData(geojsonData);

            // Apply distance-based coloring with time threshold filtering
            currentMap.setPaintProperty('statistical-areas-fill', 'fill-color', [
              'case',
              ['all',
                ['has', 'distance_ratio'],
                ['!=', ['get', 'distance_ratio'], null],
                ['get', 'is_within_threshold']  // Only show areas within driving time threshold
              ],
              [
                'case',
                ['<', ['number', ['get', 'distance_ratio']], 0.33],
                ['rgba', 16, 185, 129, 1], // Green for short distances (0-33%)
                ['<', ['number', ['get', 'distance_ratio']], 0.67],
                ['rgba', 245, 158, 11, 1], // Orange for medium distances (33-67%)
                ['rgba', 239, 68, 68, 1]  // Red for long distances (67-100%)
              ],
              ['rgba', 0, 0, 0, 0] // Transparent for areas outside threshold or without valid distance
            ]);

            // Also hide the fill opacity for areas outside threshold
            currentMap.setPaintProperty('statistical-areas-fill', 'fill-opacity', [
              'case',
              ['all',
                ['has', 'is_within_threshold'],
                ['get', 'is_within_threshold']
              ],
              0.3, // Normal opacity for areas within threshold
              0    // Fully transparent for areas outside threshold
            ]);

            console.log(`Applied distance coloring. Max distance: ${Math.round(maxDistance)} km`);
          } else {
            // Reset to default blue coloring
            currentMap.setPaintProperty('statistical-areas-fill', 'fill-color', '#3B82F6');
            console.log('Reset to default blue coloring');
          }

          // Show the layers
          currentMap.setLayoutProperty('statistical-areas-boundaries', 'visibility', 'visible');
          currentMap.setLayoutProperty('statistical-areas-fill', 'visibility', 'visible');
          currentMap.setLayoutProperty('statistical-areas-highlight', 'visibility', 'visible');

        } catch (error) {
          console.error('Error loading statistical areas:', error);
        } finally {
          setStatisticalAreasLoading(false);
        }
      } else {
        // Hide the layers
        if (currentMap.getLayer('statistical-areas-boundaries')) {
          currentMap.setLayoutProperty('statistical-areas-boundaries', 'visibility', 'none');
        }
        if (currentMap.getLayer('statistical-areas-fill')) {
          currentMap.setLayoutProperty('statistical-areas-fill', 'visibility', 'none');
        }
        if (currentMap.getLayer('statistical-areas-highlight')) {
          currentMap.setLayoutProperty('statistical-areas-highlight', 'visibility', 'none');
        }
      }
    };

    loadStatisticalAreas();
  }, [showStatisticalAreas, mapReady, selectedJobCenter, distanceCalculationEnabled, averageDrivingSpeed, drivingTimeThreshold]);

  // Handle job centers toggle
  useEffect(() => {
    if (!map.current || !mapReady) return;
    const currentMap = map.current;

    const loadJobCenters = async () => {
      if (showJobCenters) {
        setJobCentersLoading(true);
        try {
          console.log('Loading job centers to map...');

          // Add source if it doesn't exist
          if (!currentMap.getSource('job-centers')) {
            const features = jobCenters.map(center => ({
              type: 'Feature' as const,
              properties: {
                id: center.id,
                name_he: center.name_he,
                name_en: center.name_en,
                address: center.address,
                estimated_employees: center.estimated_employees,
                type: center.type
              },
              geometry: {
                type: 'Point' as const,
                coordinates: [center.longitude, center.latitude]
              }
            }));

            currentMap.addSource('job-centers', {
              type: 'geojson',
              data: {
                type: 'FeatureCollection',
                features: features
              }
            });

            // Add job centers layer with building icon
            currentMap.addLayer({
              id: 'job-centers-layer',
              type: 'circle',
              source: 'job-centers',
              paint: {
                'circle-radius': 8,
                'circle-stroke-width': 2,
                'circle-stroke-color': '#ffffff',
                'circle-color': '#DC2626'  // Red color for job centers
              }
            });

            console.log('Added job centers layers to map');

            // Add click handler for job centers
            currentMap.on('click', 'job-centers-layer', (e) => {
              const f = e.features && e.features[0];
              if (!f) return;

              const props: any = f.properties || {};
              const coord = (f.geometry as any).coordinates;

              const popupContent = `
                <div dir="rtl" style="font-family:Arial,sans-serif;min-width:300px;direction:rtl;padding:8px">
                  <div style="display:flex;align-items:center;margin-bottom:12px;justify-content:space-between">
                    <span style="font-size:12px;color:#DC2626;background:#FEF2F2;padding:4px 8px;border-radius:12px;font-weight:700">מוקד תעסוקה</span>
                  </div>

                  <div style="font-size:18px;font-weight:800;color:#111827;line-height:1.2;margin-bottom:8px;text-align:right">
                    ${props.name_he || 'מוקד תעסוקה'}
                  </div>

                  <div style="font-size:14px;color:#6B7280;margin-bottom:12px;text-align:right;">
                    ${props.address || ''}
                  </div>

                  <div style="margin-bottom:12px;background:#F9FAFB;padding:8px;border-radius:8px">
                    <div style="display:flex;justify-content:space-between;align-items:center;padding:4px 0">
                      <span style="font-size:14px;color:#374151;font-weight:700;text-align:right">מספר מועסקים (הערכה)</span>
                      <span style="font-size:14px;color:#111827;font-weight:800;text-align:left">${props.estimated_employees?.toLocaleString() || 'לא ידוע'}</span>
                    </div>
                  </div>

                  <div style="display:flex;gap:8px;margin-top:12px">
                    <a href="https://www.google.com/maps?q=${coord[1]},${coord[0]}" target="_blank" rel="noopener noreferrer"
                       style="display:inline-block;font-size:12px;background:#DC2626;color:white;padding:8px 12px;border-radius:8px;text-decoration:none;flex:1;text-align:center;font-weight:700">מפות גוגל</a>
                    <a href="https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=${coord[1]},${coord[0]}" target="_blank" rel="noopener noreferrer"
                       style="display:inline-block;font-size:12px;background:#059669;color:white;padding:8px 12px;border-radius:8px;text-decoration:none;flex:1;text-align:center;font-weight:700">תצוגת רחוב</a>
                  </div>
                </div>
              `;

              new mapboxgl.Popup({ closeButton: true, offset: 15 })
                .setLngLat(coord)
                .setHTML(popupContent)
                .addTo(currentMap);
            });

            // Change cursor on hover
            currentMap.on('mouseenter', 'job-centers-layer', () => {
              currentMap.getCanvas().style.cursor = 'pointer';
            });

            currentMap.on('mouseleave', 'job-centers-layer', () => {
              currentMap.getCanvas().style.cursor = '';
            });
          } else {
            // Update existing source
            const features = jobCenters.map(center => ({
              type: 'Feature' as const,
              properties: {
                id: center.id,
                name_he: center.name_he,
                name_en: center.name_en,
                address: center.address,
                estimated_employees: center.estimated_employees,
                type: center.type
              },
              geometry: {
                type: 'Point' as const,
                coordinates: [center.longitude, center.latitude]
              }
            }));

            (currentMap.getSource('job-centers') as mapboxgl.GeoJSONSource).setData({
              type: 'FeatureCollection',
              features: features
            });
          }

          // Show the layer
          currentMap.setLayoutProperty('job-centers-layer', 'visibility', 'visible');

        } catch (error) {
          console.error('Error loading job centers:', error);
        } finally {
          setJobCentersLoading(false);
        }
      } else {
        // Hide the layer
        if (currentMap.getLayer('job-centers-layer')) {
          currentMap.setLayoutProperty('job-centers-layer', 'visibility', 'none');
        }
      }
    };

    if (jobCenters.length > 0) {
      loadJobCenters();
    }
  }, [showJobCenters, mapReady, jobCenters]);


  // Reset statistical areas coloring when distance calculation is disabled
  useEffect(() => {
    if (!map.current || !mapReady) return;

    const currentMap = map.current;

    if (!distanceCalculationEnabled && currentMap.getLayer('statistical-areas-fill')) {
      // Reset to default coloring
      currentMap.setPaintProperty('statistical-areas-fill', 'fill-color', '#3B82F6');
      currentMap.setPaintProperty('statistical-areas-fill', 'fill-opacity', 0.3);
      console.log('Reset statistical areas to default coloring');
    }
  }, [distanceCalculationEnabled, mapReady]);

  // Initialize map
  useEffect(() => {
    if (map.current) return;

    mapboxgl.accessToken = process.env.NEXT_PUBLIC_MAPBOX_TOKEN!;

    if (mapContainer.current) {
      map.current = new mapboxgl.Map({
        container: mapContainer.current,
        style: 'mapbox://styles/mapbox/streets-v12',
        center: [35.2, 31.5], // Center of Israel
        zoom: 7,
        fadeDuration: 0,
        projection: 'mercator',
        renderWorldCopies: false,
      });

      // Add navigation control (zoom buttons)
      map.current.addControl(new mapboxgl.NavigationControl(), 'top-right');

      // Set map as ready when style is loaded
      if (map.current.isStyleLoaded()) {
        console.log('Map style already loaded, setting map ready');
        setMapReady(true);
      } else {
        map.current.on('style.load', () => {
          console.log('Map style loaded, setting map ready');
          setMapReady(true);
        });
      }
    }
  }, []);

  // Render POIs as a circle layer (no DOM markers)
  useEffect(() => {
    if (!map.current || !mapReady) return;
    const currentMap = map.current;
    
    const updatePOIs = () => {
      if (!pois.length) {
        // Clear if source exists
        if (currentMap.getSource('pois')) {
          (currentMap.getSource('pois') as mapboxgl.GeoJSONSource).setData({ type: 'FeatureCollection', features: [] });
        }
        return;
      }

      const filtered = pois.filter(p => selectedTypes.includes(p.type));
      console.log('Total POIs:', pois.length);
      console.log('Selected types:', selectedTypes);
      console.log('Filtered POIs:', filtered.length);
      const fc: GeoJSON.FeatureCollection<GeoJSON.Point, any> = {
        type: 'FeatureCollection',
        features: filtered.map(p => ({
          type: 'Feature',
          properties: {
            id: p.id,
            name_he: p.name_he,
            name_en: p.name_en,
            type: p.type,
          },
          geometry: { type: 'Point', coordinates: [p.longitude, p.latitude] },
        })),
      };
      console.log('GeoJSON features:', fc.features.length);

      if (currentMap.getSource('pois')) {
        (currentMap.getSource('pois') as mapboxgl.GeoJSONSource).setData(fc as any);
      } else {
        console.log('Adding new source with data:', fc);
        currentMap.addSource('pois', { type: 'geojson', data: fc });

        // Circle layer for points
        currentMap.addLayer({
          id: 'pois-circles',
          type: 'circle',
          source: 'pois',
          paint: {
            'circle-radius': 6,
            'circle-stroke-width': 2,
            'circle-stroke-color': '#ffffff',
            'circle-color': [
              'match', ['get', 'type'],
              'schools', '#3B82F6',
              'kindergartens', '#10B981',
              'clinics', '#EF4444',
              'bus_stops', '#F59E0B',
              /* other */ '#6B7280'
            ],
          },
        });
        console.log('Added POI layer to map');

        // Popup on click
        currentMap.on('click', 'pois-circles', (e) => {
          const f = e.features && e.features[0];
          if (!f) return;
          const props: any = f.properties || {};
          const coord = (f.geometry as any).coordinates;
          new mapboxgl.Popup({ closeButton: false, offset: 10 })
            .setLngLat(coord)
            .setHTML(
              `<div style="font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif;min-width:220px">
                <div style="display:flex;align-items:center;margin-bottom:6px">
                  <span style="font-size:10px;color:#6B7280;text-transform:uppercase;letter-spacing:.4px;background:#F3F4F6;padding:2px 6px;border-radius:999px">${String(props.type || '').replace('_',' ')}</span>
                </div>
                <div style="font-size:15px;font-weight:700;color:#111827;line-height:1.2;margin-bottom:2px">${props.name_he || ''}</div>
                <div style="font-size:12px;color:#6B7280;margin-bottom:8px">${props.name_en || ''}</div>
                <div style="display:flex;gap:8px">
                  <a href="/details/${props.id}" target="_blank" rel="noopener noreferrer"
                     style="display:inline-block;font-size:12px;background:#2563EB;color:white;padding:6px 10px;border-radius:8px;text-decoration:none">פרטים</a>
                  <a href="https://www.google.com/maps?q=${coord[1]},${coord[0]}" target="_blank" rel="noopener noreferrer"
                     style="display:inline-block;font-size:12px;background:#6B7280;color:white;padding:6px 10px;border-radius:8px;text-decoration:none">מפה</a>
                  <a href="https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=${coord[1]},${coord[0]}" target="_blank" rel="noopener noreferrer"
                     style="display:inline-block;font-size:12px;background:#059669;color:white;padding:6px 10px;border-radius:8px;text-decoration:none">תצוגת רחוב</a>
                </div>
              </div>`
            )
            .addTo(currentMap);
        });
      }
    };

    // Since we only call this effect when mapReady is true, we know the map is ready
    console.log('Updating POIs on ready map');
    updatePOIs();
  }, [pois, selectedTypes, mapReady]);

  // Get marker color based on POI type
  const getMarkerColor = (type: string): string => {
    const colors: Record<string, string> = {
      schools: '#3B82F6',      // Blue
      kindergartens: '#10B981', // Green
      clinics: '#EF4444',      // Red
      bus_stops: '#F59E0B',    // Orange
      job_center: '#DC2626',   // Red for job centers
    };
    return colors[type] || '#6B7280';
  };

  // Handle type filter changes
  const handleTypeToggle = (type: string) => {
    if (selectedTypes.includes(type)) {
      setSelectedTypes(selectedTypes.filter(t => t !== type));
    } else {
      setSelectedTypes([...selectedTypes, type]);
    }
  };

  return (
    <div className="h-screen w-full relative bg-gray-50">
      {/* Header */}
      <div className="absolute top-0 left-0 right-0 z-20 bg-white/95 border-b border-gray-200 shadow-sm">
        <div className="flex items-center justify-between px-6 py-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Neighborhood Insights</h1>
            <p className="text-sm text-gray-600">Explore Israel's Points of Interest</p>
          </div>
          <div className="flex items-center space-x-2 text-sm text-gray-500">
            <div className="w-2 h-2 bg-green-500 rounded-full"></div>
            <span>Live Data</span>
          </div>
        </div>
      </div>
      
      {/* Filter Panel */}
      <div className="absolute top-24 right-6 z-10 bg-white/95 p-6 rounded-xl shadow-lg border border-gray-200 min-w-64">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Filters</h2>
          <div className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded-full">
            {pois.filter(p => selectedTypes.includes(p.type)).length} shown
          </div>
        </div>
        
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <div className="rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
            <span className="ml-2 text-sm text-gray-600">Loading POIs...</span>
          </div>
        ) : (
          <div className="space-y-3">
            {poiTypes.map(type => {
              const count = pois.filter(p => p.type === type).length;
              const isSelected = selectedTypes.includes(type);
              
              return (
                <label key={type} className="flex items-center space-x-3 cursor-pointer group">
                  <div className="relative">
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => handleTypeToggle(type)}
                      className="sr-only"
                    />
                    <div className={`w-5 h-5 rounded border-2 ${
                      isSelected 
                        ? 'bg-blue-600 border-blue-600' 
                        : 'border-gray-300 group-hover:border-blue-400'
                    }`}>
                      {isSelected && (
                        <svg className="w-3 h-3 text-white m-0.5" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      )}
                    </div>
                  </div>
                  
                  <div
                    className="w-4 h-4 rounded-full border-2 border-white shadow-md"
                    style={{ backgroundColor: getMarkerColor(type) }}
                  />
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-gray-900 capitalize">
                        {type.replace('_', ' ')}
                      </span>
                      <span className="text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded-full">
                        {count}
                      </span>
                    </div>
                  </div>
                </label>
              );
            })}
          </div>
        )}

        {/* Statistical Areas Toggle */}
        <div className="mt-6 pt-4 border-t border-gray-200">
          <h3 className="text-sm font-semibold text-gray-900 mb-3">Boundaries</h3>
          <label className="flex items-center space-x-3 cursor-pointer group">
            <div className="relative">
              <input
                type="checkbox"
                checked={showStatisticalAreas}
                onChange={(e) => setShowStatisticalAreas(e.target.checked)}
                className="sr-only"
              />
              <div className={`w-5 h-5 rounded border-2 ${
                showStatisticalAreas
                  ? 'bg-blue-600 border-blue-600'
                  : 'border-gray-300 group-hover:border-blue-400'
              }`}>
                {showStatisticalAreas && (
                  <svg className="w-3 h-3 text-white m-0.5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                )}
              </div>
            </div>

            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-900">
                  Statistical Areas
                </span>
                {statisticalAreasLoading && (
                  <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                )}
              </div>
              <p className="text-xs text-gray-500 mt-1">
                Show statistical area boundaries
              </p>
            </div>
          </label>

          {/* Job Centers Toggle */}
          <label className="flex items-center space-x-3 cursor-pointer group mt-4">
            <div className="relative">
              <input
                type="checkbox"
                checked={showJobCenters}
                onChange={(e) => setShowJobCenters(e.target.checked)}
                className="sr-only"
              />
              <div className={`w-5 h-5 rounded border-2 ${
                showJobCenters
                  ? 'bg-blue-600 border-blue-600'
                  : 'border-gray-300 group-hover:border-blue-400'
              }`}>
                {showJobCenters && (
                  <svg className="w-3 h-3 text-white m-0.5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                )}
              </div>
            </div>

            <div
              className="w-4 h-4 rounded border-2 border-white shadow-md"
              style={{ backgroundColor: '#DC2626' }}
            />

            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-900">
                  Job Centers
                </span>
                {jobCentersLoading && (
                  <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                )}
              </div>
              <p className="text-xs text-gray-500 mt-1">
                Show major employment centers ({jobCenters.length})
              </p>
            </div>
          </label>
        </div>

        {/* Distance Calculation Section */}
        <div className="mt-6 pt-4 border-t border-gray-200">
          <h3 className="text-sm font-semibold text-gray-900 mb-3">Distance Analysis</h3>

          {/* Job Center Dropdown */}
          <div className="mb-4">
            <label className="block text-xs font-medium text-gray-700 mb-2">
              Select Job Center (מוקד תעסוקה)
            </label>
            <select
              value={selectedJobCenter?.id || ''}
              onChange={(e) => {
                const jobCenter = jobCenters.find(center => center.id === parseInt(e.target.value));
                setSelectedJobCenter(jobCenter || null);
              }}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">Choose a job center...</option>
              {jobCenters.map(jobCenter => (
                <option key={jobCenter.id} value={jobCenter.id}>
                  {jobCenter.name_he} ({jobCenter.estimated_employees.toLocaleString()} employees)
                </option>
              ))}
            </select>
          </div>

          {/* Enable Distance Calculation Toggle */}
          {selectedJobCenter && (
            <label className="flex items-center space-x-3 cursor-pointer group">
              <div className="relative">
                <input
                  type="checkbox"
                  checked={distanceCalculationEnabled}
                  onChange={(e) => setDistanceCalculationEnabled(e.target.checked)}
                  className="sr-only"
                />
                <div className={`w-5 h-5 rounded border-2 ${
                  distanceCalculationEnabled
                    ? 'bg-blue-600 border-blue-600'
                    : 'border-gray-300 group-hover:border-blue-400'
                }`}>
                  {distanceCalculationEnabled && (
                    <svg className="w-3 h-3 text-white m-0.5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  )}
                </div>
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-900">
                    Color by Distance
                  </span>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  Color areas by distance from {selectedJobCenter.name_he}
                </p>
              </div>
            </label>
          )}

          {/* Distance Legend */}
          {distanceCalculationEnabled && selectedJobCenter && (
            <div className="mt-4 p-3 bg-gray-50 rounded-lg">
              <div className="text-xs font-medium text-gray-700 mb-2">Distance Legend</div>
              <div className="space-y-1">
                <div className="flex items-center space-x-2">
                  <div className="w-4 h-4 rounded" style={{ backgroundColor: '#10B981' }}></div>
                  <span className="text-xs text-gray-600">Close (0-33%)</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-4 h-4 rounded" style={{ backgroundColor: '#F59E0B' }}></div>
                  <span className="text-xs text-gray-600">Medium (33-67%)</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-4 h-4 rounded" style={{ backgroundColor: '#EF4444' }}></div>
                  <span className="text-xs text-gray-600">Far (67-100%)</span>
                </div>
              </div>
            </div>
          )}

          {/* Driving Time Controls */}
          {distanceCalculationEnabled && selectedJobCenter && (
            <div className="mt-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
              <div className="text-xs font-semibold text-gray-900 mb-3">Driving Time Settings</div>

              {/* Average Driving Speed */}
              <div className="mb-3">
                <label className="block text-xs font-medium text-gray-800 mb-1">
                  Average Speed (km/h)
                </label>
                <input
                  type="number"
                  min="10"
                  max="120"
                  step="5"
                  value={averageDrivingSpeed}
                  onChange={(e) => setAverageDrivingSpeed(parseInt(e.target.value) || 40)}
                  className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 text-gray-900"
                />
              </div>

              {/* Driving Time Threshold */}
              <div>
                <label className="block text-xs font-medium text-gray-800 mb-1">
                  Time Threshold (minutes)
                </label>
                <input
                  type="number"
                  min="5"
                  max="120"
                  step="5"
                  value={drivingTimeThreshold}
                  onChange={(e) => setDrivingTimeThreshold(parseInt(e.target.value) || 30)}
                  className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 text-gray-900"
                />
                <p className="text-xs text-gray-700 mt-1">
                  Only show areas within {drivingTimeThreshold} minutes drive
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Quick Actions */}
        <div className="mt-6 pt-4 border-t border-gray-200">
          <div className="flex space-x-2">
            <button
              onClick={() => setSelectedTypes(poiTypes)}
              className="flex-1 text-xs py-2 px-3 bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100"
            >
              Show All
            </button>
            <button
              onClick={() => setSelectedTypes([])}
              className="flex-1 text-xs py-2 px-3 bg-gray-50 text-gray-700 rounded-lg hover:bg-gray-100"
            >
              Hide All
            </button>
          </div>
        </div>
      </div>

      <div ref={mapContainer} className="h-full w-full" style={{ marginTop: '80px' }} />
    </div>
  );
}
