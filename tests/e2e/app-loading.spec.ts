import { test, expect } from '@playwright/test';
import { TestHelpers } from '../utils/test-helpers';

test.describe('App Loading and Basic Functionality', () => {
  test('should load the application without errors', async ({ page }) => {
    const helpers = new TestHelpers(page);
    const errorMonitor = await helpers.checkForConsoleErrors();

    // Navigate to the app
    await page.goto('/');
    
    // Wait for the page to load completely
    await helpers.waitForLoadingComplete();

    // Check that the main app elements are present
    await expect(page.locator('h1')).toContainText('Level Up Your');
    
    // Verify no console errors occurred
    errorMonitor.assertNoErrors();

    // Take screenshot for visual verification
    await helpers.takeScreenshot('app-loaded');
  });

  test('should display login/authentication UI', async ({ page }) => {
    const helpers = new TestHelpers(page);
    
    await page.goto('/');
    await helpers.waitForLoadingComplete();

    // Should show login options or authenticated state
    const hasLoginButton = await helpers.isElementVisible('text=Login with Steam');
    const hasUserProfile = await helpers.isElementVisible('[data-testid="user-profile"]');
    
    // Either login button or user profile should be visible
    expect(hasLoginButton || hasUserProfile).toBeTruthy();
  });

  test('should have working navigation', async ({ page }) => {
    const helpers = new TestHelpers(page);
    
    await page.goto('/');
    await helpers.waitForLoadingComplete();

    // Check if navigation tabs are present
    const tabs = ['Overview', 'AI Analysis', 'Training', 'System'];
    
    for (const tab of tabs) {
      const tabExists = await helpers.isElementVisible(`text=${tab}`);
      if (tabExists) {
        console.log(`✓ Found tab: ${tab}`);
      }
    }

    // At least some navigation should be present
    const hasNavigation = await helpers.isElementVisible('nav') || 
                          await helpers.isElementVisible('[role="tablist"]') ||
                          await helpers.isElementVisible('.tab');
    
    expect(hasNavigation).toBeTruthy();
  });

  test('should connect to backend API', async ({ page }) => {
    const helpers = new TestHelpers(page);
    
    await page.goto('/');
    
    // Try to make a basic API call to check connectivity
    const response = await page.request.get('http://localhost:8000/health');
    expect(response.ok()).toBeTruthy();
    
    const healthData = await response.json();
    expect(healthData.status).toBe('healthy');
  });
});
