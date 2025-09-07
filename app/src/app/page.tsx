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

  // Fetch POI data from backend
  useEffect(() => {
    const fetchPOIs = async () => {
      try {
        const response = await fetch('/api/pois');
        const data = await response.json();
        // Coerce to numbers and hard-filter to Israel bounding box
        const cleaned: POI[] = data.pois
          .map((p: any) => ({
            ...p,
            longitude: Number(p.longitude),
            latitude: Number(p.latitude),
          }))
          .filter((p: POI) =>
            p.latitude >= 29.0 && p.latitude <= 33.8 &&
            p.longitude >= 33.5 && p.longitude <= 36.5
          );
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
  }, []);

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
        maxBounds: [
          [33.5, 29.0], // SW (lng, lat)
          [36.5, 33.8], // NE (lng, lat)
        ],
      });

      // Add navigation control (zoom buttons)
      map.current.addControl(new mapboxgl.NavigationControl(), 'top-right');
    }
  }, []);

  // Render POIs as a circle layer (no DOM markers)
  useEffect(() => {
    if (!map.current) return;
    const currentMap = map.current;
    if (!pois.length) {
      // Clear if source exists
      if (currentMap.getSource('pois')) {
        (currentMap.getSource('pois') as mapboxgl.GeoJSONSource).setData({ type: 'FeatureCollection', features: [] });
      }
      return;
    }

    const filtered = pois.filter(p => selectedTypes.includes(p.type));
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

    if (currentMap.getSource('pois')) {
      (currentMap.getSource('pois') as mapboxgl.GeoJSONSource).setData(fc as any);
    } else {
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
  }, [pois, selectedTypes]);

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
