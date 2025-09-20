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

export default function Home() {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);
  const [pois, setPois] = useState<POI[]>([]);
  const [poiTypes, setPOITypes] = useState<string[]>([]);
  const [selectedTypes, setSelectedTypes] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [mapReady, setMapReady] = useState(false);
  const [showStatisticalAreas, setShowStatisticalAreas] = useState(false);
  const [statisticalAreasLoading, setStatisticalAreasLoading] = useState(false);

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
          console.log('Statistical areas loaded:', geojsonData);

          // Add source if it doesn't exist
          if (!currentMap.getSource('statistical-areas')) {
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

            // Add fill layer (areas) with low opacity
            currentMap.addLayer({
              id: 'statistical-areas-fill',
              type: 'fill',
              source: 'statistical-areas',
              paint: {
                'fill-color': '#3B82F6',
                'fill-opacity': 0.1
              }
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
                  ${props['שם_יישוב_אנגלית'] ? `<div style="font-size:16px;color:#6B7280;margin-bottom:20px;text-align:right;font-weight:600">${props['שם_יישוב_אנגלית']}</div>` : ''}

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
  }, [showStatisticalAreas, mapReady]);

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
