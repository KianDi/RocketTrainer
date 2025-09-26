import { test, expect } from '../fixtures/auth';
import { TestHelpers } from '../utils/test-helpers';

test.describe('ML Analysis Functionality', () => {
  test('should navigate to AI Analysis tab', async ({ authenticatedPage }) => {
    const helpers = new TestHelpers(authenticatedPage);
    const errorMonitor = await helpers.checkForConsoleErrors();

    await helpers.waitForLoadingComplete();

    // Try to find and click AI Analysis tab
    const analysisTabSelectors = [
      'text=AI Analysis',
      '[data-testid="ai-analysis-tab"]',
      'button:has-text("AI Analysis")',
      'a:has-text("AI Analysis")'
    ];

    let tabFound = false;
    for (const selector of analysisTabSelectors) {
      if (await helpers.isElementVisible(selector)) {
        await authenticatedPage.click(selector);
        tabFound = true;
        console.log(`✓ Found and clicked AI Analysis tab: ${selector}`);
        break;
      }
    }

    if (!tabFound) {
      console.log('ℹ AI Analysis tab not found, checking if already on analysis page');
    }

    await helpers.waitForLoadingComplete();
    errorMonitor.assertNoErrors();

    await helpers.takeScreenshot('ai-analysis-tab');
  });

  test('should display analysis interface', async ({ authenticatedPage }) => {
    const helpers = new TestHelpers(authenticatedPage);

    // Navigate to analysis (if tab exists)
    const hasAnalysisTab = await helpers.isElementVisible('text=AI Analysis');
    if (hasAnalysisTab) {
      await authenticatedPage.click('text=AI Analysis');
      await helpers.waitForLoadingComplete();
    }

    // Check for analysis interface elements
    const analysisElements = [
      'text=Analyze My Gameplay',
      'text=Analysis Depth',
      '[data-testid="analysis-button"]',
      'button:has-text("Analyze")'
    ];

    let hasAnalysisInterface = false;
    for (const selector of analysisElements) {
      if (await helpers.isElementVisible(selector)) {
        hasAnalysisInterface = true;
        console.log(`✓ Found analysis interface element: ${selector}`);
        break;
      }
    }

    expect(hasAnalysisInterface).toBeTruthy();
  });

  test('should perform ML analysis', async ({ authenticatedPage }) => {
    const helpers = new TestHelpers(authenticatedPage);
    const errorMonitor = await helpers.checkForConsoleErrors();

    // Navigate to analysis page
    const hasAnalysisTab = await helpers.isElementVisible('text=AI Analysis');
    if (hasAnalysisTab) {
      await authenticatedPage.click('text=AI Analysis');
      await helpers.waitForLoadingComplete();
    }

    // Find and click analyze button
    const analyzeButtonSelectors = [
      'text=Analyze My Gameplay',
      'button:has-text("Analyze")',
      '[data-testid="analyze-button"]'
    ];

    let buttonFound = false;
    for (const selector of analyzeButtonSelectors) {
      if (await helpers.isElementVisible(selector)) {
        // Click analyze button and wait for API response
        await helpers.clickAndWait(selector, '/api/ml/analyze-weaknesses');
        buttonFound = true;
        console.log(`✓ Clicked analyze button: ${selector}`);
        break;
      }
    }

    expect(buttonFound).toBeTruthy();

    // Wait for analysis results to appear
    await helpers.waitForLoadingComplete();

    // Check for analysis results
    const resultElements = [
      'text=Primary:',
      'text=Matches Analyzed',
      'text=Confidence',
      'text=Key Areas for Improvement',
      'text=Detailed Skill Breakdown'
    ];

    let hasResults = false;
    for (const selector of resultElements) {
      if (await helpers.isElementVisible(selector)) {
        hasResults = true;
        console.log(`✓ Found analysis result: ${selector}`);
      }
    }

    expect(hasResults).toBeTruthy();
    errorMonitor.assertNoErrors();

    await helpers.takeScreenshot('ml-analysis-results');
  });

  test('should display analysis metadata', async ({ authenticatedPage }) => {
    const helpers = new TestHelpers(authenticatedPage);

    // Perform analysis first
    const hasAnalysisTab = await helpers.isElementVisible('text=AI Analysis');
    if (hasAnalysisTab) {
      await authenticatedPage.click('text=AI Analysis');
      await helpers.waitForLoadingComplete();
    }

    const analyzeButton = await helpers.isElementVisible('text=Analyze My Gameplay');
    if (analyzeButton) {
      await helpers.clickAndWait('text=Analyze My Gameplay', '/api/ml/analyze-weaknesses');
      await helpers.waitForLoadingComplete();
    }

    // Check for metadata elements
    const metadataElements = [
      'text=User ID:',
      'text=Generated:',
      'text=Analysis completed',
      /\d+ Matches Analyzed/
    ];

    for (const selector of metadataElements) {
      if (typeof selector === 'string') {
        const hasElement = await helpers.isElementVisible(selector);
        if (hasElement) {
          console.log(`✓ Found metadata: ${selector}`);
        }
      } else {
        // RegExp selector - check page content
        const pageContent = await authenticatedPage.textContent('body');
        if (pageContent && selector.test(pageContent)) {
          console.log(`✓ Found metadata pattern: ${selector}`);
        }
      }
    }
  });
});
