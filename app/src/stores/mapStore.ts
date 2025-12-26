import { create } from 'zustand';
import mapboxgl from 'mapbox-gl';

interface MapStore {
  // Map instance
  map: mapboxgl.Map | null;
  mapReady: boolean;

  // Actions
  setMap: (map: mapboxgl.Map) => void;
  setMapReady: (ready: boolean) => void;
}

export const useMapStore = create<MapStore>((set) => ({
  // Initial state
  map: null,
  mapReady: false,

  // Actions
  setMap: (map) => set({ map }),
  setMapReady: (ready) => set({ mapReady: ready }),
}));
