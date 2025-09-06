import { render, screen } from '@testing-library/react'
import Map from '../../src/components/Map'

// Mock mapbox-gl module
jest.mock('mapbox-gl', () => ({
  Map: jest.fn(() => ({
    addControl: jest.fn(),
    on: jest.fn((event, callback) => {
      if (event === 'load') {
        setTimeout(callback, 0)
      }
    }),
    remove: jest.fn(),
  })),
  NavigationControl: jest.fn(),
  AttributionControl: jest.fn(),
  Marker: jest.fn(() => ({
    setLngLat: jest.fn(() => ({
      setPopup: jest.fn(() => ({
        addTo: jest.fn(),
      })),
      addTo: jest.fn(),
    })),
  })),
  Popup: jest.fn(() => ({
    setHTML: jest.fn(() => ({
      setOffset: jest.fn(),
    })),
  })),
  accessToken: '',
}))

describe('Map Component', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders map container', () => {
    render(<Map />)
    
    const mapContainer = screen.getByTestId('mapbox-container')
    expect(mapContainer).toBeInTheDocument()
  })

  it('applies custom className', () => {
    const customClass = 'custom-map-class'
    render(<Map className={customClass} />)
    
    const mapContainer = screen.getByTestId('mapbox-container')
    expect(mapContainer).toHaveClass(customClass)
  })

  it('initializes mapbox when token is provided', () => {
    process.env.NEXT_PUBLIC_MAPBOX_TOKEN = 'pk.test.token'
    
    render(<Map />)
    
    // Map should be initialized with correct token
    const mapboxgl = jest.requireMock('mapbox-gl')
    expect(mapboxgl.accessToken).toBe('pk.test.token')
  })

  it('handles missing mapbox token gracefully', () => {
    const originalToken = process.env.NEXT_PUBLIC_MAPBOX_TOKEN
    delete process.env.NEXT_PUBLIC_MAPBOX_TOKEN
    
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {})
    
    render(<Map />)
    
    expect(consoleSpy).toHaveBeenCalledWith(
      'Mapbox token is required. Set NEXT_PUBLIC_MAPBOX_TOKEN environment variable.'
    )
    
    consoleSpy.mockRestore()
    process.env.NEXT_PUBLIC_MAPBOX_TOKEN = originalToken
  })

  it('has correct default styles and attributes', () => {
    render(<Map />)
    
    const mapContainer = screen.getByTestId('mapbox-container')
    expect(mapContainer).toHaveClass('w-full', 'h-full')
  })
})