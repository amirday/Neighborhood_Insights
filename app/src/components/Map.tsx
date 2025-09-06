"use client";

import { useEffect, useRef } from 'react';
import mapboxgl from 'mapbox-gl';

// Import Mapbox CSS
import 'mapbox-gl/dist/mapbox-gl.css';

interface MapProps {
  className?: string;
}

// Israeli bounds for initial view
const ISRAEL_BOUNDS: [[number, number], [number, number]] = [
  [34.2, 29.5], // Southwest coordinates
  [35.9, 33.4], // Northeast coordinates
];

const ISRAEL_CENTER: [number, number] = [35.2137, 31.7683]; // Jerusalem coordinates

export default function Map({ className = "" }: MapProps) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);
  const hoveredIdRef = useRef<number | string | null>(null);

  useEffect(() => {
    if (map.current) return; // Initialize map only once

    // Set Mapbox access token
    mapboxgl.accessToken = process.env.NEXT_PUBLIC_MAPBOX_TOKEN || '';

    if (!mapboxgl.accessToken) {
      console.error('Mapbox token is required. Set NEXT_PUBLIC_MAPBOX_TOKEN environment variable.');
      return;
    }

    if (!mapContainer.current) return;

    // Ensure the container is empty to avoid Mapbox GL warning and interaction issues
    try {
      mapContainer.current.innerHTML = '';
    } catch {}

    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: 'mapbox://styles/mapbox/light-v11',
      center: ISRAEL_CENTER,
      zoom: 7,
      maxBounds: ISRAEL_BOUNDS,
      attributionControl: false,
      antialias: false,
      dragRotate: false,
      cooperativeGestures: true,
    });

    // Add navigation control
    map.current.addControl(new mapboxgl.NavigationControl(), 'top-right');

    // Add attribution control
    map.current.addControl(
      new mapboxgl.AttributionControl({
        customAttribution: 'Neighborhood Insights IL',
      })
    );

    // Handle map load event
    map.current.on('load', () => {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL;
      const dataUrl = apiUrl
        ? `${apiUrl.replace(/\/$/, '')}/regions/geojson?simplify=0.0005`
        : '/data/neighborhoods.sample.geojson';
      // Helpful during debugging
      try { console.log('Loading neighborhoods from:', dataUrl); } catch {}
      // Neighborhoods source (Day 9 local GeoJSON; Day 10 will switch to API/tiles)
      try {
        // Add the source with empty data first; then fetch and set data.
        const src: any = {
          type: 'geojson',
          data: { type: 'FeatureCollection', features: [] },
        };
        if (apiUrl) {
          src.promoteId = 'region_id';
        } else {
          src.generateId = true; // for local sample
        }
        map.current?.addSource('neighborhoods', src);

        // Fill layer with hover-dependent color/opacity
        map.current?.addLayer({
          id: 'hood-fill',
          type: 'fill',
          source: 'neighborhoods',
          paint: {
            'fill-color': [
              'case',
              ['boolean', ['feature-state', 'hover'], false], '#2563EB', '#60A5FA',
            ],
            'fill-opacity': [
              'case',
              ['boolean', ['feature-state', 'hover'], false], 0.35, 0.2,
            ],
          },
        } as any);

        // Outline layer for clarity
        map.current?.addLayer({
          id: 'hood-outline',
          type: 'line',
          source: 'neighborhoods',
          paint: {
            'line-color': '#1E3A8A',
            'line-width': [
              'interpolate', ['linear'], ['zoom'],
              7, 0.5,
              12, 1.25,
              15, 2,
            ],
            'line-opacity': 0.7,
          },
        } as any);

        // Hover highlight
        map.current?.on('mousemove', 'hood-fill', (e) => {
          if (!map.current) return;
          map.current.getCanvas().style.cursor = 'pointer';
          const f = e.features?.[0];
          if (!f) return;
          const id = (f.id as number | string) ?? (f.properties as any)?.id;
          if (hoveredIdRef.current !== null && hoveredIdRef.current !== id) {
            map.current.setFeatureState(
              { source: 'neighborhoods', id: hoveredIdRef.current },
              { hover: false }
            );
          }
          hoveredIdRef.current = id as any;
          map.current.setFeatureState(
            { source: 'neighborhoods', id },
            { hover: true }
          );
        });

        map.current?.on('mouseleave', 'hood-fill', () => {
          if (!map.current) return;
          map.current.getCanvas().style.cursor = '';
          if (hoveredIdRef.current !== null) {
            map.current.setFeatureState(
              { source: 'neighborhoods', id: hoveredIdRef.current },
              { hover: false }
            );
          }
          hoveredIdRef.current = null;
        });

        // Load data into the source (with API fallback handling)
        const loadData = async () => {
          const source = map.current?.getSource('neighborhoods') as mapboxgl.GeoJSONSource | undefined;
          if (!source) return;
          try {
            const res = await fetch(dataUrl, { mode: 'cors' });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const gj = await res.json();
            source.setData(gj);
          } catch (err) {
            console.error('Failed to load from API, falling back to local sample:', err);
            try {
              const res2 = await fetch('/data/neighborhoods.sample.geojson');
              const gj2 = await res2.json();
              source.setData(gj2);
            } catch (err2) {
              console.error('Failed to load fallback sample GeoJSON:', err2);
            }
          }
        };
        loadData();

        // Popup helper (RTL content)
        const openPopup = (lngLat: mapboxgl.LngLatLike, props: Record<string, any>) => {
          new mapboxgl.Popup({ offset: 10, closeButton: true })
            .setLngLat(lngLat)
            .setHTML(
              `<div dir="rtl" class="p-2">
                 <h3 class="font-semibold">${props.name_he ?? props.name_en ?? 'אזור סטטיסטי'}</h3>
                 ${props.population ? `<p>אוכלוסייה: ${Number(props.population).toLocaleString('he-IL')}</p>` : ''}
               </div>`
            )
            .addTo(map.current!);
        };

        // Click & touch interactions
        map.current?.on('click', 'hood-fill', (e) => {
          const f = e.features?.[0];
          if (f) openPopup(e.lngLat, (f.properties || {}) as any);
        });
        map.current?.on('touchend', 'hood-fill', (e) => {
          const f = (e as any).features?.[0] || e.features?.[0];
          const lngLat = (e as any).lngLat ?? (e as any).points?.[0]?.lngLat;
          if (f && lngLat) openPopup(lngLat, (f.properties || {}) as any);
        });
      } catch (err) {
        console.error('Failed to initialize neighborhood layers:', err);
      }
    });

    map.current.on('error', (e) => {
      console.error('Map error:', e);
    });

    return () => {
      if (map.current) {
        map.current.remove();
        map.current = null;
      }
    };
  }, []);

  return (
    <div 
      ref={mapContainer} 
      className={`w-full h-full ${className}`}
      data-testid="mapbox-container"
    />
  );
}
