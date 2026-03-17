import "@testing-library/jest-dom";

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};

global.localStorage = localStorageMock;

// Mock fetch
global.fetch = jest.fn();

// Mock window.location.href setter to avoid JSDOM navigation errors
global.mockLocationHrefSetter = jest.fn();

// Delete the existing location and create a new one with proper href setter
delete window.location;

// Create mock location with href as a getter/setter that calls our spy
const mockLocation = {};

// Add all the standard location properties
Object.assign(mockLocation, {
  assign: jest.fn(),
  reload: jest.fn(),
  replace: jest.fn(),
  toString: jest.fn(() => "http://localhost/"),
  origin: "http://localhost",
  protocol: "http:",
  host: "localhost",
  hostname: "localhost",
  port: "",
  pathname: "/",
  search: "",
  hash: "",
  _href: "http://localhost/",
});

// Define the href property with getter/setter
Object.defineProperty(mockLocation, "href", {
  get() {
    return this._href;
  },
  set(value) {
    this._href = value;
    global.mockLocationHrefSetter(value);
  },
  configurable: true,
  enumerable: true,
});

// Set window.location to our mock
window.location = mockLocation;

// Clean up after each test
afterEach(() => {
  jest.clearAllMocks();
  // Reset the href setter spy too
  if (global.mockLocationHrefSetter) {
    global.mockLocationHrefSetter.mockClear();
  }
});
