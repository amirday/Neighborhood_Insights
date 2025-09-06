import '@testing-library/jest-dom'

// Mock mapbox-gl
jest.mock('mapbox-gl', () => ({
  Map: jest.fn(() => ({
    addControl: jest.fn(),
    on: jest.fn(),
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

// Mock next/dynamic
jest.mock('next/dynamic', () => (fn) => {
  const DynamicComponent = fn()
  return DynamicComponent
})

// Setup global mocks
global.ResizeObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}))

// Mock environment variables
process.env.NEXT_PUBLIC_MAPBOX_TOKEN = 'pk.test.token'