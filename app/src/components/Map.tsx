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

  useEffect(() => {
    if (map.current) return; // Initialize map only once

    // Set Mapbox access token
    mapboxgl.accessToken = process.env.NEXT_PUBLIC_MAPBOX_TOKEN || '';

    if (!mapboxgl.accessToken) {
      console.error('Mapbox token is required. Set NEXT_PUBLIC_MAPBOX_TOKEN environment variable.');
      return;
    }

    if (!mapContainer.current) return;

    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: 'mapbox://styles/mapbox/light-v11',
      center: ISRAEL_CENTER,
      zoom: 7,
      maxBounds: ISRAEL_BOUNDS,
      attributionControl: false,
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
      console.log('Map loaded successfully');
      
      // Add a simple marker for Jerusalem as example
      if (map.current) {
        new mapboxgl.Marker({ color: '#3B82F6' })
          .setLngLat(ISRAEL_CENTER)
          .setPopup(
            new mapboxgl.Popup({ offset: 25 })
              .setHTML('<div class="p-2"><h3 class="font-semibold">ירושלים</h3><p>בירת ישראל</p></div>')
          )
          .addTo(map.current);
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