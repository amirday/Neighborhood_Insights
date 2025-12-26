'use client';

import { useRef, useEffect } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import { useMapStore } from '@/stores/mapStore';

interface MapViewProps {
  className?: string;
}

export function MapView({ className = '' }: MapViewProps) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const mapRef = useRef<mapboxgl.Map | null>(null);
  const setMap = useMapStore((state) => state.setMap);
  const setMapReady = useMapStore((state) => state.setMapReady);

  useEffect(() => {
    if (mapRef.current) return;

    mapboxgl.accessToken = process.env.NEXT_PUBLIC_MAPBOX_TOKEN!;

    if (mapContainer.current) {
      mapRef.current = new mapboxgl.Map({
        container: mapContainer.current,
        style: 'mapbox://styles/mapbox/light-v11',
        center: [35.2, 31.5], // Center of Israel
        zoom: 7,
        fadeDuration: 0,
        projection: 'mercator',
        renderWorldCopies: false,
      });

      // Add navigation control (zoom buttons)
      mapRef.current.addControl(new mapboxgl.NavigationControl(), 'top-right');

      // Store map instance in Zustand
      setMap(mapRef.current);

      // Set map as ready when style is loaded
      if (mapRef.current.isStyleLoaded()) {
        console.log('Map style already loaded, setting map ready');
        setMapReady(true);
      } else {
        mapRef.current.on('style.load', () => {
          console.log('Map style loaded, setting map ready');
          setMapReady(true);
        });
      }
    }

    // Add ESC key handler to close popups
    const handleEscKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape' || e.key === 'Esc') {
        const popups = document.querySelectorAll('.mapboxgl-popup');
        popups.forEach(popup => popup.remove());
      }
    };

    document.addEventListener('keydown', handleEscKey);

    // Cleanup
    return () => {
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
      document.removeEventListener('keydown', handleEscKey);
    };
  }, [setMap, setMapReady]);

  return (
    <div
      ref={mapContainer}
      className={`h-full w-full ${className}`}
      style={{ marginTop: 'var(--header-height)' }}
    />
  );
}
