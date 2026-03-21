import { test, expect } from '@playwright/test';
import { test as authTest } from '../fixtures/auth';

authTest.describe('@int_auth Auth smoke tests', () => {
  test('health check - API server is running', async ({ request }) => {
    // This is the only non-todo test - simple smoke test to verify stack is running
    const response = await request.get('/api/health');
    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body.status).toBe('healthy');
  });

  test.todo('user can log in via Google OAuth');

  test.todo('user can log in via Twitter OAuth');

  test.todo('user can view profile information after login');

  test.todo('user can log out successfully');

  test.todo('logged out user is redirected to login page when accessing protected routes');

  test.todo('authentication state persists across browser sessions');

  test.todo('expired tokens are refreshed automatically');

  test.todo('invalid tokens trigger re-authentication flow');

  authTest.describe('Authenticated User Flows', () => {
    authTest.todo('authenticated user can access protected pages');

    authTest.todo('authenticated user sees correct navigation menu');

    authTest.todo('user profile displays correct information');
  });
});