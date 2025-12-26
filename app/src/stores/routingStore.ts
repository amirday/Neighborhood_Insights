import { create } from 'zustand';
import { JobCenter } from '@/types';

interface RoutingStore {
  // State
  selectedJobCenter: JobCenter | null;
  jobCenters: JobCenter[];
  jobCenterTypes: string[];
  selectedJobCenterTypes: string[];
  distanceCalculationEnabled: boolean;
  routesCalculationEnabled: boolean;
  routesLoading: boolean;
  routingStats: any | null;
  routingError: string | null;
  averageDrivingSpeed: number; // km/h
  drivingTimeThreshold: number; // minutes

  // Actions
  setSelectedJobCenter: (center: JobCenter | null) => void;
  setJobCenters: (centers: JobCenter[]) => void;
  toggleJobCenterType: (type: string) => void;
  selectAllJobCenterTypes: () => void;
  clearAllJobCenterTypes: () => void;
  setDistanceCalculationEnabled: (enabled: boolean) => void;
  setRoutesCalculationEnabled: (enabled: boolean) => void;
  setRoutesLoading: (loading: boolean) => void;
  setRoutingStats: (stats: any) => void;
  setRoutingError: (error: string | null) => void;
  setAverageDrivingSpeed: (speed: number) => void;
  setDrivingTimeThreshold: (threshold: number) => void;
}

export const useRoutingStore = create<RoutingStore>((set, get) => ({
  // Initial state
  selectedJobCenter: null,
  jobCenters: [],
  jobCenterTypes: [],
  selectedJobCenterTypes: [],
  distanceCalculationEnabled: false,
  routesCalculationEnabled: false,
  routesLoading: false,
  routingStats: null,
  routingError: null,
  averageDrivingSpeed: 40, // Default: 40 km/h
  drivingTimeThreshold: 30, // Default: 30 minutes

  // Actions
  setSelectedJobCenter: (center) => set({ selectedJobCenter: center }),
  setJobCenters: (centers) => {
    const types = Array.from(new Set(centers.map((c) => c.type)));
    set({
      jobCenters: centers,
      jobCenterTypes: types,
      selectedJobCenterTypes: types, // Show all types by default
    });
  },
  toggleJobCenterType: (type) =>
    set((state) => ({
      selectedJobCenterTypes: state.selectedJobCenterTypes.includes(type)
        ? state.selectedJobCenterTypes.filter((t) => t !== type)
        : [...state.selectedJobCenterTypes, type],
    })),
  selectAllJobCenterTypes: () =>
    set((state) => ({ selectedJobCenterTypes: state.jobCenterTypes })),
  clearAllJobCenterTypes: () => set({ selectedJobCenterTypes: [] }),
  setDistanceCalculationEnabled: (enabled) =>
    set({ distanceCalculationEnabled: enabled }),
  setRoutesCalculationEnabled: (enabled) =>
    set({ routesCalculationEnabled: enabled }),
  setRoutesLoading: (loading) => set({ routesLoading: loading }),
  setRoutingStats: (stats) =>
    set({ routingStats: stats, routingError: null }),
  setRoutingError: (error) =>
    set({ routingError: error, routingStats: null, routesLoading: false }),
  setAverageDrivingSpeed: (speed) => set({ averageDrivingSpeed: speed }),
  setDrivingTimeThreshold: (threshold) =>
    set({ drivingTimeThreshold: threshold }),
}));
