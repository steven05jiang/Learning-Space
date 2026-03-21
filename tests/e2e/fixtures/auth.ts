import { test as base, expect, Page } from '@playwright/test';

export interface AuthenticatedUser {
  email: string;
  name: string;
  id: string;
}

// Extend basic test by providing an authenticated page fixture
export const test = base.extend<{
  authenticatedPage: Page;
  currentUser: AuthenticatedUser;
}>({
  authenticatedPage: async ({ page }, use) => {
    // Navigate to login page
    await page.goto('/login');

    // TODO: Replace with actual OAuth login flow when implemented
    // For now, this is a placeholder that assumes auth is working
    await page.waitForLoadState('networkidle');

    // Mock authenticated state by setting localStorage/cookies
    await page.evaluate(() => {
      // This will be replaced with actual auth token handling
      localStorage.setItem('user', JSON.stringify({
        id: 'test-user-123',
        email: 'test@example.com',
        name: 'Test User'
      }));
    });

    await use(page);
  },

  currentUser: async ({}, use) => {
    const user: AuthenticatedUser = {
      id: 'test-user-123',
      email: 'test@example.com',
      name: 'Test User'
    };
    await use(user);
  }
});

export { expect } from '@playwright/test';