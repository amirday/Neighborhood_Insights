import dynamic from 'next/dynamic';

// Dynamically import Map component to avoid SSR issues with Mapbox
const Map = dynamic(() => import('../components/Map'), {
  ssr: false,
  loading: () => (
    <div className="w-full h-full flex items-center justify-center bg-gray-100">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-2"></div>
        <p className="text-gray-600">טוען מפה...</p>
      </div>
    </div>
  ),
});

export default function Home() {
  return (
    <div className="relative w-full h-[calc(100vh-80px)]">
      {/* Desktop search panel */}
      <div className="hidden md:flex absolute top-4 left-4 z-10 bg-white rounded-lg shadow-lg p-4 max-w-sm">
        <div className="text-right">
          <h2 className="text-lg font-semibold mb-2 text-gray-800">חיפוש שכונות</h2>
          <p className="text-sm text-gray-600 mb-4">
            גלה שכונות בישראל על בסיס איכות חיים, חינוך, ביטחון ושירותים
          </p>
          <div className="space-y-2">
            <input
              type="text"
              placeholder="חיפוש לפי כתובת..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-right"
            />
            <button className="w-full bg-blue-600 text-white py-2 rounded-md hover:bg-blue-700 transition-colors">
              חיפוש
            </button>
          </div>
        </div>
      </div>
      
      {/* Map takes full available height */}
      <div className="w-full h-full">
        <Map className="w-full h-full" />
      </div>
      
      {/* Mobile search bar */}
      <div className="md:hidden fixed bottom-4 left-4 right-4 z-10 bg-white rounded-lg shadow-lg p-4">
        <div className="flex gap-2">
          <input
            type="text"
            placeholder="חיפוש שכונה..."
            className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-right"
          />
          <button className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors">
            חיפוש
          </button>
        </div>
      </div>
    </div>
  );
}
