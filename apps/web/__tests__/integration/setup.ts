import '@testing-library/jest-dom';

// Mock fetch for integration tests
const mockFetch = jest.fn();
global.fetch = mockFetch;

// Test setup utilities
export { mockFetch };

// Mock data exports for easy access in tests
export * from './mocks/auth';
export * from './mocks/resources';
export * from './mocks/graph';
export * from './mocks/chat';

// Reset mocks before each test
beforeEach(() => {
  mockFetch.mockClear();
});

// Clean up after each test
afterEach(() => {
  jest.clearAllMocks();
});