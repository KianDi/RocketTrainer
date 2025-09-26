import { Page, expect } from '@playwright/test';

/**
 * Test helper utilities for RocketTrainer E2E tests
 */

export class TestHelpers {
  constructor(private page: Page) {}

  /**
   * Wait for API request to complete and check for errors
   */
  async waitForApiRequest(urlPattern: string | RegExp, timeout = 10000) {
    const responsePromise = this.page.waitForResponse(
      response => {
        const url = response.url();
        if (typeof urlPattern === 'string') {
          return url.includes(urlPattern);
        }
        return urlPattern.test(url);
      },
      { timeout }
    );

    const response = await responsePromise;
    expect(response.ok()).toBeTruthy();
    return response;
  }

  /**
   * Check for JavaScript console errors
   */
  async checkForConsoleErrors() {
    const errors: string[] = [];
    
    this.page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    this.page.on('pageerror', error => {
      errors.push(error.message);
    });

    return {
      getErrors: () => errors,
      hasErrors: () => errors.length > 0,
      assertNoErrors: () => {
        if (errors.length > 0) {
          throw new Error(`Console errors found: ${errors.join(', ')}`);
        }
      }
    };
  }

  /**
   * Wait for loading states to complete
   */
  async waitForLoadingComplete() {
    // Wait for network to be idle
    await this.page.waitForLoadState('networkidle');
    
    // Wait for any loading spinners to disappear
    await this.page.waitForFunction(() => {
      const spinners = document.querySelectorAll('[data-testid="loading"], .animate-spin, .loading');
      return spinners.length === 0;
    }, { timeout: 10000 }).catch(() => {
      // Ignore timeout - loading spinners might not exist
    });
  }

  /**
   * Click and wait for navigation/response
   */
  async clickAndWait(selector: string, waitForResponse?: string | RegExp) {
    if (waitForResponse) {
      const responsePromise = this.waitForApiRequest(waitForResponse);
      await this.page.click(selector);
      await responsePromise;
    } else {
      await this.page.click(selector);
      await this.waitForLoadingComplete();
    }
  }

  /**
   * Check if element exists and is visible
   */
  async isElementVisible(selector: string): Promise<boolean> {
    try {
      const element = this.page.locator(selector);
      await element.waitFor({ state: 'visible', timeout: 5000 });
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Get text content safely
   */
  async getTextContent(selector: string): Promise<string> {
    const element = this.page.locator(selector);
    await element.waitFor({ state: 'visible' });
    return await element.textContent() || '';
  }

  /**
   * Take screenshot with timestamp
   */
  async takeScreenshot(name: string) {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    await this.page.screenshot({ 
      path: `test-results/screenshots/${name}-${timestamp}.png`,
      fullPage: true 
    });
  }
}
