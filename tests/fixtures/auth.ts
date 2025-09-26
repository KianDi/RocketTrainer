import { test as base, expect } from '@playwright/test';

/**
 * Authentication fixtures for RocketTrainer tests
 * Provides authenticated user context using debug tokens
 */

export interface AuthFixtures {
  authenticatedPage: any;
  testUser: {
    username: string;
    userId: string;
    token: string;
  };
}

export const test = base.extend<AuthFixtures>({
  testUser: async ({}, use) => {
    // Use the test user we created earlier
    const testUser = {
      username: 'kyan1',
      userId: '6b342dbc-28c3-43c3-93f3-e9415ac22d3d',
      token: '' // Will be fetched dynamically
    };
    await use(testUser);
  },

  authenticatedPage: async ({ page, testUser }, use) => {
    // Get debug token for test user
    const tokenResponse = await page.request.get(`http://localhost:8000/auth/debug-token/${testUser.username}`);
    expect(tokenResponse.ok()).toBeTruthy();
    
    const tokenData = await tokenResponse.json();
    testUser.token = tokenData.access_token;

    // Set up authentication by storing token in localStorage
    await page.goto('/');
    
    // Wait for the page to load
    await page.waitForLoadState('networkidle');
    
    // Inject authentication token into localStorage
    await page.evaluate((token) => {
      localStorage.setItem('auth_token', token);
      localStorage.setItem('user_data', JSON.stringify({
        id: '6b342dbc-28c3-43c3-93f3-e9415ac22d3d',
        username: 'kyan1',
        email: 'test@example.com'
      }));
    }, testUser.token);

    // Reload to apply authentication
    await page.reload();
    await page.waitForLoadState('networkidle');

    await use(page);
  },
});

export { expect } from '@playwright/test';
