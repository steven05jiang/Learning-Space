// Auth mock data and utilities
export const mockUser = {
  id: 'user_123',
  email: 'test@example.com',
  name: 'Test User',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

export const mockAuthResponse = {
  access_token: 'mock_jwt_token',
  user: mockUser,
};

export const authMockHandlers = {
  login: () =>
    Promise.resolve({
      ok: true,
      json: () => Promise.resolve(mockAuthResponse),
    }),

  logout: () =>
    Promise.resolve({
      ok: true,
      json: () => Promise.resolve({ message: 'Logged out successfully' }),
    }),

  profile: () =>
    Promise.resolve({
      ok: true,
      json: () => Promise.resolve(mockUser),
    }),

  googleCallback: () =>
    Promise.resolve({
      ok: true,
      url: 'http://localhost:3000/dashboard?auth=success',
    }),

  refreshToken: () =>
    Promise.resolve({
      ok: true,
      json: () => Promise.resolve({ access_token: 'new_mock_jwt_token' }),
    }),
};