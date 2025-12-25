'use client';

import { useRef, useEffect } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';

interface MapViewProps {
  onMapReady: (map: mapboxgl.Map) => void;
  className?: string;
}

export function MapView({ onMapReady, className = '' }: MapViewProps) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);

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
        onMapReady(map.current);
      } else {
        map.current.on('style.load', () => {
          console.log('Map style loaded, setting map ready');
          if (map.current) {
            onMapReady(map.current);
          }
        });
      }
    }
  }, [onMapReady]);

  return (
    <div
      ref={mapContainer}
      className={`h-full w-full ${className}`}
      style={{ marginTop: 'var(--header-height)' }}
    />
  );
}
