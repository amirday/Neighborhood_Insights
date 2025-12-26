import { create } from 'zustand';
import { POI } from '@/types';

interface POIStore {
  // State
  pois: POI[];
  poiTypes: string[];
  selectedTypes: string[];
  loading: boolean;
  error: string | null;

  // Actions
  setPOIs: (pois: POI[]) => void;
  toggleType: (type: string) => void;
  selectAllTypes: () => void;
  clearAllTypes: () => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

export const usePOIStore = create<POIStore>((set, get) => ({
  // Initial state
  pois: [],
  poiTypes: [],
  selectedTypes: [],
  loading: false,
  error: null,

  // Actions
  setPOIs: (pois) => {
    const types = Array.from(new Set(pois.map((p) => p.type)));
    set({
      pois,
      poiTypes: types,
      selectedTypes: [], // Hide all types by default
      loading: false,
      error: null,
    });
  },

  toggleType: (type) =>
    set((state) => ({
      selectedTypes: state.selectedTypes.includes(type)
        ? state.selectedTypes.filter((t) => t !== type)
        : [...state.selectedTypes, type],
    })),

  selectAllTypes: () => set((state) => ({ selectedTypes: state.poiTypes })),

  clearAllTypes: () => set({ selectedTypes: [] }),

  setLoading: (loading) => set({ loading }),

  setError: (error) => set({ error, loading: false }),
}));
