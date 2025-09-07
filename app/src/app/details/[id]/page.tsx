"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";

type POI = {
  id: number;
  name_he: string;
  name_en: string;
  type: string;
  longitude: number;
  latitude: number;
  address?: string;
  symbol?: string;
};

export default function DetailsPage() {
  const params = useParams<{ id: string }>();
  const [poi, setPoi] = useState<POI | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const id = params?.id;
    if (!id) return;
    fetch(`/api/pois/${id}`)
      .then((r) => r.json())
      .then((data) => setPoi(data))
      .catch((e) => setError(String(e)));
  }, [params?.id]);

  if (error) {
    return <div className="p-6">Error: {error}</div>;
  }
  if (!poi) {
    return <div className="min-h-screen flex items-center justify-center text-gray-500">טוען…</div>;
  }

  const mapsUrl = `https://www.google.com/maps?q=${poi.latitude},${poi.longitude}`;
  const streetViewUrl = `https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=${poi.latitude},${poi.longitude}`;

  return (
    <div className="min-h-screen bg-gray-50" dir="rtl">
      <div className="max-w-3xl mx-auto p-6">
        {/* Header */}
        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm mb-6">
          <div className="flex items-start justify-between">
            <div>
              <div className="text-xs text-gray-500 mb-1">מוסד חינוכי</div>
              <h1 className="text-2xl font-bold text-gray-900">{poi.name_he}</h1>
              <div className="text-sm text-gray-600 mt-1">{poi.name_en}</div>
            </div>
            <span className="text-xs bg-blue-50 text-blue-700 px-2 py-1 rounded-full capitalize">{poi.type}</span>
          </div>
        </div>

        {/* Info cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          {poi.address && (
            <div className="bg-white rounded-xl border p-4">
              <div className="text-xs text-gray-500 mb-1">כתובת</div>
              <div className="text-sm">{poi.address}</div>
            </div>
          )}
          {poi.symbol && (
            <div className="bg-white rounded-xl border p-4">
              <div className="text-xs text-gray-500 mb-1">סמל מוסד</div>
              <div className="text-sm">{poi.symbol}</div>
            </div>
          )}
          <div className="bg-white rounded-xl border p-4">
            <div className="text-xs text-gray-500 mb-1">מיקום</div>
            <div className="text-sm">{poi.latitude}, {poi.longitude}</div>
          </div>
        </div>

        {/* Actions */}
        <div className="flex flex-wrap gap-2">
          <a
            className="px-4 py-2 bg-blue-600 text-white rounded-lg shadow-sm"
            href={mapsUrl}
            target="_blank"
            rel="noopener noreferrer"
          >
            פתח במפות
          </a>
          <a
            className="px-4 py-2 bg-emerald-600 text-white rounded-lg shadow-sm"
            href={streetViewUrl}
            target="_blank"
            rel="noopener noreferrer"
          >
            תצוגת רחוב
          </a>
          <a className="px-4 py-2 bg-gray-100 text-gray-800 rounded-lg" href="/">
            חזרה למפה
          </a>
        </div>
      </div>
    </div>
  );
}
