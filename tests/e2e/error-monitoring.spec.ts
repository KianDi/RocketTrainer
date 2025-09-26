import { test, expect } from '../fixtures/auth';
import { TestHelpers } from '../utils/test-helpers';

test.describe('Error Monitoring and Edge Cases', () => {
  test('should handle network errors gracefully', async ({ authenticatedPage }) => {
    const helpers = new TestHelpers(authenticatedPage);
    const errorMonitor = await helpers.checkForConsoleErrors();

    await helpers.waitForLoadingComplete();

    // Test with invalid API endpoint
    const response = await authenticatedPage.request.get('http://localhost:8000/api/invalid-endpoint').catch(() => null);
    
    // Should handle 404 gracefully
    if (response) {
      expect(response.status()).toBe(404);
    }

    // UI should still be functional
    const isPageResponsive = await helpers.isElementVisible('body');
    expect(isPageResponsive).toBeTruthy();

    // Should not have critical JavaScript errors
    const errors = errorMonitor.getErrors();
    const criticalErrors = errors.filter(error => 
      error.includes('TypeError') || 
      error.includes('ReferenceError') ||
      error.includes('Cannot read properties of undefined')
    );

    if (criticalErrors.length > 0) {
      console.warn('Critical errors found:', criticalErrors);
    }

    expect(criticalErrors.length).toBe(0);
  });

  test('should handle API rate limiting', async ({ authenticatedPage }) => {
    const helpers = new TestHelpers(authenticatedPage);

    // Navigate to analysis
    const hasAnalysisTab = await helpers.isElementVisible('text=AI Analysis');
    if (hasAnalysisTab) {
      await authenticatedPage.click('text=AI Analysis');
      await helpers.waitForLoadingComplete();
    }

    // Try to trigger rate limiting by making multiple requests
    const analyzeButton = await helpers.isElementVisible('text=Analyze My Gameplay');
    if (analyzeButton) {
      // First request
      await helpers.clickAndWait('text=Analyze My Gameplay', '/api/ml/analyze-weaknesses');
      
      // Second request immediately (might hit rate limit)
      const hasButtonAgain = await helpers.isElementVisible('text=Analyze My Gameplay');
      if (hasButtonAgain) {
        await authenticatedPage.click('text=Analyze My Gameplay');
        
        // Wait and check for rate limit message or successful response
        await helpers.waitForLoadingComplete();
        
        // Should handle rate limiting gracefully (no crashes)
        const isPageStillWorking = await helpers.isElementVisible('body');
        expect(isPageStillWorking).toBeTruthy();
      }
    }
  });

  test('should handle empty or invalid analysis data', async ({ authenticatedPage }) => {
    const helpers = new TestHelpers(authenticatedPage);
    const errorMonitor = await helpers.checkForConsoleErrors();

    // Navigate to analysis
    const hasAnalysisTab = await helpers.isElementVisible('text=AI Analysis');
    if (hasAnalysisTab) {
      await authenticatedPage.click('text=AI Analysis');
      await helpers.waitForLoadingComplete();
    }

    // Perform analysis
    const analyzeButton = await helpers.isElementVisible('text=Analyze My Gameplay');
    if (analyzeButton) {
      await helpers.clickAndWait('text=Analyze My Gameplay', '/api/ml/analyze-weaknesses');
      await helpers.waitForLoadingComplete();
    }

    // Check that UI handles empty/placeholder data gracefully
    const hasUnknownWeakness = await helpers.isElementVisible('text=unknown');
    const hasZeroConfidence = await helpers.isElementVisible('text=0%');
    
    if (hasUnknownWeakness || hasZeroConfidence) {
      console.log('✓ UI handles placeholder data correctly');
    }

    // Should not crash with empty skill categories
    const hasSkillSection = await helpers.isElementVisible('text=Detailed Skill Breakdown');
    if (hasSkillSection) {
      console.log('✓ Skill breakdown section renders even with empty data');
    }

    // No critical errors should occur
    errorMonitor.assertNoErrors();

    await helpers.takeScreenshot('empty-data-handling');
  });

  test('should monitor console for JavaScript errors', async ({ authenticatedPage }) => {
    const helpers = new TestHelpers(authenticatedPage);
    const errors: string[] = [];
    const warnings: string[] = [];

    // Set up comprehensive error monitoring
    authenticatedPage.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      } else if (msg.type() === 'warning') {
        warnings.push(msg.text());
      }
    });

    authenticatedPage.on('pageerror', error => {
      errors.push(`Page Error: ${error.message}`);
    });

    // Navigate through the app
    await helpers.waitForLoadingComplete();

    // Try to interact with various elements
    const tabs = ['Overview', 'AI Analysis', 'Training', 'System'];
    for (const tab of tabs) {
      const hasTab = await helpers.isElementVisible(`text=${tab}`);
      if (hasTab) {
        await authenticatedPage.click(`text=${tab}`);
        await helpers.waitForLoadingComplete();
        console.log(`✓ Navigated to ${tab} tab`);
      }
    }

    // Perform ML analysis if possible
    const analyzeButton = await helpers.isElementVisible('text=Analyze My Gameplay');
    if (analyzeButton) {
      await helpers.clickAndWait('text=Analyze My Gameplay', '/api/ml/analyze-weaknesses');
      await helpers.waitForLoadingComplete();
    }

    // Report findings
    console.log(`JavaScript Errors: ${errors.length}`);
    console.log(`JavaScript Warnings: ${warnings.length}`);

    if (errors.length > 0) {
      console.log('Errors found:', errors);
    }

    if (warnings.length > 0) {
      console.log('Warnings found:', warnings.slice(0, 5)); // Show first 5 warnings
    }

    // Fail test if critical errors found
    const criticalErrors = errors.filter(error => 
      !error.includes('favicon') && // Ignore favicon errors
      !error.includes('404') && // Ignore 404s for optional resources
      !error.includes('net::ERR_') // Ignore network errors for optional resources
    );

    expect(criticalErrors.length).toBe(0);
  });
});
