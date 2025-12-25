// Shared type definitions for the application

export interface POI {
  id: number;
  name_he: string;
  name_en: string;
  type: string;
  longitude: number;
  latitude: number;
  address?: string;
  symbol?: string;
}

export interface JobCenter {
  id: number;
  name_he: string;
  name_en: string;
  address: string;
  estimated_employees: number;
  type: string;
  longitude: number;
  latitude: number;
}

export interface StatisticalAreaProperties {
  OBJECTID: number;
  שם_יישוב: string;
  שם_יישוב_אנגלית?: string;
  סוג_יישוב?: string;
  אזור_גיאוגרפי?: string;
  distance_km?: number;
  driving_time_minutes?: number;
  is_within_threshold?: boolean;
  route_time_driving?: number;
  route_time_cycling?: number;
  route_time_walking?: number;
  route_time_transit?: number;
  distance_ratio?: number;
  [key: string]: any;
}

export interface RouteResult {
  success: boolean;
  duration_minutes?: number;
  distance_km?: number;
  geometry?: Array<[number, number]>;
  error?: string;
  method?: string;
}

export type TransportMode = 'driving' | 'cycling' | 'walking' | 'transit';

export type POIType = 'schools' | 'kindergartens' | 'clinics' | 'bus_stops';
