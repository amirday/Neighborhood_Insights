'use client';

import { useEffect } from 'react';
import { Header } from '@/components/Header/Header';
import { MapView } from '@/components/MapView/MapView';
import { POILayer } from '@/components/map/layers/POILayer';
import { StatisticalAreasLayer } from '@/components/map/layers/StatisticalAreasLayer';
import { JobCentersLayer } from '@/components/map/layers/JobCentersLayer';
import { RoutingAnalysisPanel } from '@/components/RoutingAnalysis/RoutingAnalysisPanel';
import { BottomSheet } from '@/components/BottomSheet/BottomSheet';
import { POITypeFilter } from '@/components/filters/POITypeFilter';
import { QuickActions } from '@/components/filters/QuickActions';
import { JobCenterTypeFilter } from '@/components/filters/JobCenterTypeFilter';
import { JobCenterQuickActions } from '@/components/filters/JobCenterQuickActions';
import { SelectedJobCenter } from '@/components/filters/SelectedJobCenter';
import { useResponsive } from '@/hooks/useResponsive';
import { useMapStore } from '@/stores/mapStore';
import { usePOIStore } from '@/stores/poiStore';
import { useRoutingStore } from '@/stores/routingStore';
import { useToast } from '@/hooks/ui/useToast';

export default function Home() {
  const { isMobile } = useResponsive();
  const toast = useToast();

  // Map store
  const mapReady = useMapStore((state) => state.mapReady);

  // POI store
  const setPOIs = usePOIStore((state) => state.setPOIs);
  const setLoading = usePOIStore((state) => state.setLoading);
  const setError = usePOIStore((state) => state.setError);
  const selectedTypes = usePOIStore((state) => state.selectedTypes);
  const pois = usePOIStore((state) => state.pois);

  // Routing store
  const setJobCenters = useRoutingStore((state) => state.setJobCenters);
  const selectedJobCenter = useRoutingStore((state) => state.selectedJobCenter);
  const routesCalculationEnabled = useRoutingStore((state) => state.routesCalculationEnabled);
  const setRoutesCalculationEnabled = useRoutingStore((state) => state.setRoutesCalculationEnabled);
  const routesLoading = useRoutingStore((state) => state.routesLoading);
  const routingStats = useRoutingStore((state) => state.routingStats);
  const routingError = useRoutingStore((state) => state.routingError);

  // Fetch POIs when map is ready
  useEffect(() => {
    if (!mapReady) return;

    const fetchPOIs = async () => {
      setLoading(true);
      try {
        console.log('Fetching POIs...');
        const response = await fetch('/api/pois');
        const data = await response.json();

        if (!data.pois || !Array.isArray(data.pois)) {
          throw new Error('Invalid POI data received');
        }

        // Clean and filter POIs to Israel bounding box
        const cleaned = data.pois
          .map((p: any) => ({
            ...p,
            longitude: Number(p.longitude),
            latitude: Number(p.latitude),
          }))
          .filter(
            (p: any) =>
              p.latitude >= 29.0 &&
              p.latitude <= 33.8 &&
              p.longitude >= 34.2 &&
              p.longitude <= 35.9
          );

        console.log(`Loaded ${cleaned.length} POIs`);
        setPOIs(cleaned);
        toast.success('POIs loaded', `${cleaned.length} locations loaded successfully`);
      } catch (error) {
        console.error('Error fetching POIs:', error);
        setError('Failed to load POIs');
        toast.error('Failed to load POIs', 'Please refresh the page');
      }
    };

    fetchPOIs();
  }, [mapReady]); // Only depend on mapReady - Zustand actions are stable

  // Fetch job centers when map is ready
  useEffect(() => {
    if (!mapReady) return;

    const fetchJobCenters = async () => {
      try {
        console.log('Fetching job centers...');
        const response = await fetch('http://localhost:8000/job-centers');
        const data = await response.json();

        if (!data.job_centers || !Array.isArray(data.job_centers)) {
          console.error('No job centers data received from API');
          return;
        }

        console.log(`Loaded ${data.job_centers.length} job centers`);
        setJobCenters(data.job_centers);
      } catch (error) {
        console.error('Error fetching job centers:', error);
        toast.error('Failed to load job centers');
      }
    };

    fetchJobCenters();
  }, [mapReady]); // Only depend on mapReady - Zustand actions are stable

  // Calculate routes handler
  const handleCalculateRoutes = async () => {
    // TODO: Implement route calculation logic
    console.log('Calculate routes clicked');
  };

  // Calculate filtered POI count
  const filteredPOICount = pois.filter((p) => selectedTypes.includes(p.type)).length;

  return (
    <div className="relative h-screen overflow-hidden" style={{ background: 'var(--color-base)' }}>
      {/* Header */}
      <Header poiCount={filteredPOICount} />

      {/* Map */}
      <MapView />

      {/* Map Layers - invisible components that manage map layers */}
      <POILayer />
      <StatisticalAreasLayer />
      <JobCentersLayer />

      {/* Desktop Filter Panel */}
      {!isMobile && (
        <div
          className="fixed grid-bg overflow-y-auto animate-slide-in-right"
          style={{
            top: 'calc(var(--header-height) + 1.5rem)',
            right: '1.5rem',
            bottom: '1.5rem',
            zIndex: 'var(--z-filter-panel)',
            width: 'min(28rem, calc(100vw - 3rem))',
            background: 'var(--color-surface)',
            border: '4px solid var(--color-border)',
            boxShadow: '8px 8px 0 var(--color-bright-coral)',
            animationDelay: '0.2s',
            opacity: 0,
          }}
        >
          {/* Panel Header with diagonal accent */}
          <div
            className="sticky top-0 px-6 py-5 z-10"
            style={{
              background: 'var(--color-surface)',
              borderBottom: '3px solid var(--color-bright-coral)',
            }}
          >
            <div className="flex items-center gap-3">
              <div
                style={{
                  width: '6px',
                  height: '40px',
                  background: 'var(--color-bright-coral)',
                  transform: 'skewX(-10deg)',
                }}
              />
              <h2
                className="text-display"
                style={{
                  fontSize: '2rem',
                  color: 'var(--color-text-primary)',
                  letterSpacing: '0.05em',
                }}
              >
                FILTERS
              </h2>
            </div>
          </div>

          <div className="p-6 space-y-6">
            {/* Quick Actions */}
            <div>
              <h3
                className="text-mono uppercase mb-3"
                style={{
                  fontSize: '0.75rem',
                  color: 'var(--color-bright-coral)',
                  letterSpacing: '0.1em',
                  fontWeight: 700,
                }}
              >
                QUICK ACTIONS
              </h3>
              <QuickActions />
            </div>

            {/* Divider */}
            <div
              style={{
                height: '2px',
                background: 'var(--color-border-light)',
              }}
            />

            {/* POI Type Filter */}
            <div>
              <h3
                className="text-mono uppercase mb-3"
                style={{
                  fontSize: '0.75rem',
                  color: 'var(--color-sky-blue)',
                  letterSpacing: '0.1em',
                  fontWeight: 700,
                }}
              >
                POI TYPES
              </h3>
              <POITypeFilter />
            </div>

            {/* Divider */}
            <div
              style={{
                height: '2px',
                background: 'var(--color-border-light)',
              }}
            />

            {/* Job Center Type Filter */}
            <div>
              <h3
                className="text-mono uppercase mb-3"
                style={{
                  fontSize: '0.75rem',
                  color: 'var(--color-deep-purple)',
                  letterSpacing: '0.1em',
                  fontWeight: 700,
                }}
              >
                JOB CENTERS
              </h3>
              <div className="space-y-3">
                <SelectedJobCenter />
                <JobCenterQuickActions />
                <JobCenterTypeFilter />
              </div>
            </div>
          </div>
        </div>
      )}


      {/* Mobile Bottom Sheet */}
      {isMobile && (
        <BottomSheet title="Filters" defaultExpanded={false}>
          <div className="space-y-6">
            <QuickActions />
            <POITypeFilter />
            <div>
              <h3 className="text-sm font-semibold text-gray-900 mb-3">Job Centers</h3>
              <div className="mb-3">
                <SelectedJobCenter />
              </div>
              <div className="mb-3">
                <JobCenterQuickActions />
              </div>
              <JobCenterTypeFilter />
            </div>
            {/* TODO: Add full mobile experience in Phase 3 */}
          </div>
        </BottomSheet>
      )}

      {/* TODO: Add ToastContainer in Phase 5 */}
    </div>
  );
}
