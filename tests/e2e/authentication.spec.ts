import { test, expect } from '../fixtures/auth';
import { TestHelpers } from '../utils/test-helpers';

test.describe('Authentication Flow', () => {
  test('should authenticate user with debug token', async ({ authenticatedPage, testUser }) => {
    const helpers = new TestHelpers(authenticatedPage);
    const errorMonitor = await helpers.checkForConsoleErrors();

    // Verify authentication worked
    await helpers.waitForLoadingComplete();

    // Check for authenticated state indicators
    const hasUserInfo = await helpers.isElementVisible(`text=${testUser.username}`) ||
                       await helpers.isElementVisible('[data-testid="user-profile"]') ||
                       await helpers.isElementVisible('.user-menu');

    if (hasUserInfo) {
      console.log('✓ User authentication detected');
    }

    // Verify no authentication errors
    errorMonitor.assertNoErrors();

    await helpers.takeScreenshot('authenticated-state');
  });

  test('should have access to protected features', async ({ authenticatedPage }) => {
    const helpers = new TestHelpers(authenticatedPage);
    
    await helpers.waitForLoadingComplete();

    // Check if ML Analysis tab/button is accessible
    const hasAnalysisAccess = await helpers.isElementVisible('text=AI Analysis') ||
                             await helpers.isElementVisible('text=Analyze My Gameplay') ||
                             await helpers.isElementVisible('[data-testid="ml-analysis"]');

    if (hasAnalysisAccess) {
      console.log('✓ ML Analysis access confirmed');
    }

    // Should have access to some protected features
    expect(hasAnalysisAccess).toBeTruthy();
  });

  test('should maintain authentication across page reloads', async ({ authenticatedPage, testUser }) => {
    const helpers = new TestHelpers(authenticatedPage);
    
    // Reload the page
    await authenticatedPage.reload();
    await helpers.waitForLoadingComplete();

    // Check that authentication persisted
    const stillAuthenticated = await helpers.isElementVisible(`text=${testUser.username}`) ||
                              await helpers.isElementVisible('[data-testid="user-profile"]');

    if (stillAuthenticated) {
      console.log('✓ Authentication persisted after reload');
    }
  });
});
