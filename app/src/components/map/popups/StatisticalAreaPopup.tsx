'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { useRoutingStore } from '@/stores/routingStore';
import { useMapStore } from '@/stores/mapStore';
import mapboxgl from 'mapbox-gl';

interface Props {
  properties: any;
  coordinates: { lat: number; lng: number };
}

type TransportMode = 'driving' | 'cycling' | 'walking' | 'transit';

/**
 * StatisticalAreaPopup Component
 *
 * Displays information about a statistical area when clicked on the map.
 * Includes distance information, area details, and route calculation options.
 */
export function StatisticalAreaPopup({ properties, coordinates }: Props) {
  const selectedJobCenter = useRoutingStore((state) => state.selectedJobCenter);
  const map = useMapStore((state) => state.map);
  const [routeResult, setRouteResult] = useState<string | null>(null);
  const [isCalculating, setIsCalculating] = useState(false);

  const areaId = properties.OBJECTID;
  const mainTitle = properties.שם_יישוב || properties.SHEM_YISHU || properties.SHEM_YIS_1 || 'אזור סטטיסטי';
  const googleMapsUrl = `https://www.google.com/maps?q=${coordinates.lat},${coordinates.lng}`;
  const streetViewUrl = `https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=${coordinates.lat},${coordinates.lng}`;

  // Field mapping for display
  const fieldMapping = [
    { key: 'distance_km', name: 'מרחק ממוקד התעסוקה', suffix: ' ק"מ' },
    { key: 'driving_time_minutes', name: 'זמן נסיעה משוער (קו אוויר)', suffix: ' דקות' },
    { key: 'שם_יישוב', name: 'שם יישוב' },
    { key: 'שם_יישוב_אנגלית', name: 'שם יישוב באנגלית' },
    { key: 'סוג_יישוב', name: 'סוג יישוב' },
    { key: 'אזור_גיאוגרפי', name: 'אזור גיאוגרפי' },
  ];

  const displayProps = fieldMapping
    .map((field) => {
      const value = properties[field.key];
      if (value === null || value === undefined || value === '' || (typeof value === 'number' && isNaN(value))) {
        return null;
      }

      let displayValue = value;
      if (typeof value === 'number') {
        displayValue = field.suffix ? `${value.toLocaleString()}${field.suffix}` : value.toLocaleString();
      }

      return { name: field.name, value: displayValue };
    })
    .filter((item) => item !== null);

  const handleCalculateRoute = async (mode: TransportMode) => {
    if (!selectedJobCenter || !map) return;

    setIsCalculating(true);
    setRouteResult('מחשב מסלול...');

    try {
      const url = `http://localhost:8000/routes/area-to-center?center_id=${selectedJobCenter.id}&area_id=${areaId}&modes=${mode}&include_geometry=true`;
      const response = await fetch(url);
      const data = await response.json();

      if (data.error) {
        setRouteResult(data.error);
        return;
      }

      const result = data.results?.[mode];
      if (result && result.success) {
        const mins = result.duration_minutes?.toLocaleString() ?? result.duration_minutes;
        const dist = result.distance_km?.toLocaleString() ?? result.distance_km;
        let message = `זמן ${mode}: ${mins} דקות · מרחק: ${dist} ק"מ`;

        if (mode === 'transit' && result.method === 'heuristic_driving_x2') {
          message += ' (הערכה על בסיס זמן נסיעה ברכב ×2)';
        }

        setRouteResult(message);

        // Render route on map
        if (result.geometry && map) {
          // Remove previous preview
          if (map.getLayer('route-preview')) {
            map.removeLayer('route-preview');
          }
          if (map.getSource('route-preview-src')) {
            map.removeSource('route-preview-src');
          }

          if (result.geometry.length >= 2) {
            // Convert [lat,lon] -> [lon,lat]
            const lineCoords = result.geometry.map((p: number[]) => [p[1], p[0]]);

            map.addSource('route-preview-src', {
              type: 'geojson',
              data: {
                type: 'Feature',
                geometry: { type: 'LineString', coordinates: lineCoords },
                properties: {},
              },
            });

            map.addLayer({
              id: 'route-preview',
              type: 'line',
              source: 'route-preview-src',
              paint: {
                'line-color': '#10B981',
                'line-width': 4,
                'line-opacity': 0.9,
              },
            });
          }
        }
      } else {
        setRouteResult(result?.error || 'חישוב נכשל');
      }
    } catch (error) {
      console.error('Route calculation error:', error);
      setRouteResult('שגיאה בחישוב המסלול');
    } finally {
      setIsCalculating(false);
    }
  };

  return (
    <div dir="rtl" className="min-w-[280px] max-w-[min(500px,92vw)] p-4">
      {/* Header badges */}
      <div className="flex items-center gap-2 mb-4">
        <span className="text-xs font-bold text-sky-700 bg-sky-100 px-3 py-1.5 rounded-full">
          אזור סטטיסטי
        </span>
        {properties.אזור_גיאוגרפי && (
          <span className="text-xs font-bold text-emerald-700 bg-emerald-100 px-3 py-1.5 rounded-full">
            {properties.אזור_גיאוגרפי}
          </span>
        )}
      </div>

      {/* Main title */}
      <h3 className="text-xl font-bold text-gray-900 mb-2">{mainTitle}</h3>
      {properties.שם_יישוב_אנגלית && (
        <p className="text-base text-gray-600 mb-4 font-semibold">{properties.שם_יישוב_אנגלית}</p>
      )}

      {/* Distance info card */}
      {properties.distance_km && (
        <div className="mb-4 p-3 bg-gradient-to-br from-amber-50 to-orange-50 rounded-xl border border-amber-200">
          <div className="text-sm font-semibold text-gray-700 mb-1">מרחק ממוקד התעסוקה הנבחר</div>
          <div className="text-2xl font-bold text-orange-700">{properties.distance_km} ק"מ</div>
          {properties.driving_time_minutes && (
            <div className="text-sm text-gray-600 mt-1">
              זמן נסיעה משוער: {properties.driving_time_minutes} דקות
            </div>
          )}
        </div>
      )}

      {/* Route calculation section */}
      {selectedJobCenter ? (
        <div className="mb-4 p-3 bg-emerald-50 rounded-xl border border-emerald-200">
          <div className="text-sm font-bold text-emerald-800 mb-2">
            חישוב מסלול אל {selectedJobCenter.name_he}
          </div>
          <div className="flex gap-2 flex-wrap mb-2">
            <Button
              size="sm"
              className="bg-emerald-600 hover:bg-emerald-700 text-white"
              onClick={() => handleCalculateRoute('driving')}
              disabled={isCalculating}
            >
              🚗 רכב
            </Button>
            <Button
              size="sm"
              className="bg-blue-600 hover:bg-blue-700 text-white"
              onClick={() => handleCalculateRoute('cycling')}
              disabled={isCalculating}
            >
              🚴 אופניים
            </Button>
            <Button
              size="sm"
              className="bg-amber-600 hover:bg-amber-700 text-white"
              onClick={() => handleCalculateRoute('walking')}
              disabled={isCalculating}
            >
              🚶 הליכה
            </Button>
            <Button
              size="sm"
              className="bg-violet-600 hover:bg-violet-700 text-white"
              onClick={() => handleCalculateRoute('transit')}
              disabled={isCalculating}
            >
              🚌 תחבורה
            </Button>
          </div>
          {routeResult && (
            <div className="text-sm text-emerald-800 font-medium">{routeResult}</div>
          )}
        </div>
      ) : (
        <div className="mb-4 p-3 bg-amber-50 rounded-xl border border-amber-200">
          <div className="text-sm font-bold text-amber-900 mb-1">כדי לחשב מסלול נא לבחור מוקד תעסוקה</div>
          <div className="text-xs text-amber-800">בחר/י מוקד תעסוקה בלוח הצד</div>
        </div>
      )}

      {/* Area details */}
      {displayProps.length > 0 && (
        <div className="mb-4 bg-gray-50 rounded-xl p-3 space-y-2">
          {displayProps.map((item, idx) => (
            <div key={idx} className="flex justify-between items-center pb-2 border-b border-gray-200 last:border-b-0">
              <span className="text-sm font-bold text-gray-700">{item!.name}</span>
              <span className="text-sm font-extrabold text-gray-900 bg-white px-2 py-1 rounded">
                {item!.value}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Action buttons */}
      <div className="flex gap-3">
        <Button asChild variant="default" className="flex-1 bg-blue-600 hover:bg-blue-700">
          <a href={googleMapsUrl} target="_blank" rel="noopener noreferrer">
            מפות גוגל
          </a>
        </Button>
        <Button asChild variant="default" className="flex-1 bg-emerald-600 hover:bg-emerald-700">
          <a href={streetViewUrl} target="_blank" rel="noopener noreferrer">
            תצוגת רחוב
          </a>
        </Button>
      </div>
    </div>
  );
}
