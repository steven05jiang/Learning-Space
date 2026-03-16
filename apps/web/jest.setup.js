import '@testing-library/jest-dom'

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
}

global.localStorage = localStorageMock

// Mock fetch
global.fetch = jest.fn()

// Mock window.location.href setter to avoid JSDOM navigation errors
const mockLocation = {
  href: 'http://localhost/',
  assign: jest.fn(),
  reload: jest.fn(),
  replace: jest.fn(),
  toString: jest.fn(() => 'http://localhost/'),
}

delete window.location
window.location = mockLocation

// Clean up after each test
afterEach(() => {
  jest.clearAllMocks()
})