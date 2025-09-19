import { NextResponse } from 'next/server';

export async function GET() {
  try {
    // Proxy to the FastAPI backend
    const response = await fetch('http://localhost:8001/pois');
    
    if (!response.ok) {
      throw new Error(`Backend responded with status: ${response.status}`);
    }
    
    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error fetching POIs from backend:', error);
    return NextResponse.json(
      { error: 'Failed to fetch POIs' },
      { status: 500 }
    );
  }
}