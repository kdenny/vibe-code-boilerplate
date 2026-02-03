# Playwright E2E Testing

Comprehensive guide for end-to-end testing with Playwright.

## When to Use This Recipe

Use Playwright when you need to:
- Test user flows across your application
- Verify critical paths work correctly (signup, checkout, etc.)
- Catch regressions before deployment
- Test across multiple browsers (Chromium, Firefox, WebKit)

## Quick Start

### New Projects

```bash
# Initialize Playwright (interactive)
npm init playwright@latest

# Or use the setup wizard
bin/vibe setup -w playwright
```

### Existing Projects (Retrofit)

If you already have Playwright configured:

```bash
# Verify setup and get improvement suggestions
bin/vibe setup -w playwright

# Or manually verify
npx playwright --version
npx playwright test --list
```

## Project Structure

After initialization, you'll have:

```
your-project/
├── playwright.config.ts      # Main configuration
├── tests/                    # Test files
│   └── example.spec.ts
├── tests-examples/           # Example tests (can delete)
└── .github/
    └── workflows/
        └── playwright.yml    # CI workflow (if selected)
```

## Configuration

### Basic Configuration

```typescript
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  // Directory containing test files
  testDir: './tests',

  // Run tests in parallel
  fullyParallel: true,

  // Fail build on test.only() in CI
  forbidOnly: !!process.env.CI,

  // Retry failed tests in CI
  retries: process.env.CI ? 2 : 0,

  // Parallel workers
  workers: process.env.CI ? 1 : undefined,

  // Reporter configuration
  reporter: [
    ['html', { open: 'never' }],
    ['list'],
  ],

  // Shared settings for all projects
  use: {
    // Base URL for navigation
    baseURL: 'http://localhost:3000',

    // Collect trace on failure
    trace: 'on-first-retry',

    // Screenshot on failure
    screenshot: 'only-on-failure',
  },

  // Browser configurations
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
  ],

  // Run local dev server before tests
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
});
```

### Framework-Specific Base URLs

```typescript
// Next.js
baseURL: 'http://localhost:3000',

// Vite
baseURL: 'http://localhost:5173',

// Astro
baseURL: 'http://localhost:4321',

// Custom
baseURL: process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:3000',
```

### Mobile Testing

```typescript
projects: [
  // Desktop
  { name: 'chromium', use: { ...devices['Desktop Chrome'] } },

  // Mobile
  { name: 'Mobile Chrome', use: { ...devices['Pixel 5'] } },
  { name: 'Mobile Safari', use: { ...devices['iPhone 12'] } },
],
```

## Writing Tests

### Basic Test Structure

```typescript
// tests/example.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Homepage', () => {
  test('should display welcome message', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByRole('heading', { name: 'Welcome' })).toBeVisible();
  });

  test('should navigate to about page', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('link', { name: 'About' }).click();
    await expect(page).toHaveURL('/about');
  });
});
```

### Page Object Pattern

```typescript
// tests/pages/login.page.ts
import { Page, Locator } from '@playwright/test';

export class LoginPage {
  readonly page: Page;
  readonly emailInput: Locator;
  readonly passwordInput: Locator;
  readonly submitButton: Locator;
  readonly errorMessage: Locator;

  constructor(page: Page) {
    this.page = page;
    this.emailInput = page.getByLabel('Email');
    this.passwordInput = page.getByLabel('Password');
    this.submitButton = page.getByRole('button', { name: 'Sign in' });
    this.errorMessage = page.getByRole('alert');
  }

  async goto() {
    await this.page.goto('/login');
  }

  async login(email: string, password: string) {
    await this.emailInput.fill(email);
    await this.passwordInput.fill(password);
    await this.submitButton.click();
  }
}

// tests/auth.spec.ts
import { test, expect } from '@playwright/test';
import { LoginPage } from './pages/login.page';

test('successful login redirects to dashboard', async ({ page }) => {
  const loginPage = new LoginPage(page);
  await loginPage.goto();
  await loginPage.login('user@example.com', 'password123');
  await expect(page).toHaveURL('/dashboard');
});
```

### Custom Fixtures

```typescript
// tests/fixtures.ts
import { test as base } from '@playwright/test';
import { LoginPage } from './pages/login.page';

type MyFixtures = {
  loginPage: LoginPage;
  authenticatedPage: Page;
};

export const test = base.extend<MyFixtures>({
  loginPage: async ({ page }, use) => {
    const loginPage = new LoginPage(page);
    await use(loginPage);
  },

  authenticatedPage: async ({ page }, use) => {
    // Login before test
    await page.goto('/login');
    await page.getByLabel('Email').fill('test@example.com');
    await page.getByLabel('Password').fill('password');
    await page.getByRole('button', { name: 'Sign in' }).click();
    await page.waitForURL('/dashboard');
    await use(page);
  },
});

export { expect } from '@playwright/test';
```

### API Mocking

```typescript
test('displays products from API', async ({ page }) => {
  // Mock API response
  await page.route('**/api/products', async route => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([
        { id: 1, name: 'Product 1', price: 100 },
        { id: 2, name: 'Product 2', price: 200 },
      ]),
    });
  });

  await page.goto('/products');
  await expect(page.getByText('Product 1')).toBeVisible();
  await expect(page.getByText('Product 2')).toBeVisible();
});
```

### Authentication State Reuse

```typescript
// tests/auth.setup.ts
import { test as setup, expect } from '@playwright/test';

const authFile = 'playwright/.auth/user.json';

setup('authenticate', async ({ page }) => {
  await page.goto('/login');
  await page.getByLabel('Email').fill(process.env.TEST_USER_EMAIL!);
  await page.getByLabel('Password').fill(process.env.TEST_USER_PASSWORD!);
  await page.getByRole('button', { name: 'Sign in' }).click();
  await page.waitForURL('/dashboard');

  // Save authentication state
  await page.context().storageState({ path: authFile });
});

// playwright.config.ts
export default defineConfig({
  projects: [
    { name: 'setup', testMatch: /.*\.setup\.ts/ },
    {
      name: 'chromium',
      dependencies: ['setup'],
      use: {
        storageState: 'playwright/.auth/user.json',
      },
    },
  ],
});
```

## Running Tests

### Basic Commands

```bash
# Run all tests
npx playwright test

# Run specific test file
npx playwright test tests/auth.spec.ts

# Run tests with specific name
npx playwright test -g "login"

# Run in headed mode (see browser)
npx playwright test --headed

# Run in specific browser
npx playwright test --project=chromium

# Run in debug mode
npx playwright test --debug

# Run with UI mode (interactive)
npx playwright test --ui
```

### Generating Tests

```bash
# Record a new test
npx playwright codegen localhost:3000

# Record with specific browser
npx playwright codegen --browser=firefox localhost:3000

# Record to a specific file
npx playwright codegen -o tests/new-flow.spec.ts localhost:3000
```

### Viewing Reports

```bash
# View HTML report
npx playwright show-report

# View trace (after failure with trace enabled)
npx playwright show-trace test-results/*/trace.zip
```

## CI/CD Integration

### GitHub Actions (Auto-detected)

The boilerplate's test workflow automatically detects Playwright:

```yaml
# .github/workflows/tests.yml (already configured)
- name: Detect and run Playwright tests
  if: hashFiles('playwright.config.ts') != '' || hashFiles('playwright.config.js') != ''
  run: |
    npx playwright install --with-deps
    npx playwright test
```

### Custom Workflow

```yaml
# .github/workflows/e2e.yml
name: E2E Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'

      - run: npm ci

      - name: Install Playwright Browsers
        run: npx playwright install --with-deps

      - name: Run Playwright tests
        run: npx playwright test
        env:
          PLAYWRIGHT_BASE_URL: ${{ secrets.STAGING_URL }}

      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: playwright-report
          path: playwright-report/
          retention-days: 7
```

### Artifacts and Reports

```yaml
# Upload test results on failure
- uses: actions/upload-artifact@v4
  if: failure()
  with:
    name: test-results
    path: test-results/
    retention-days: 7

# Upload HTML report always
- uses: actions/upload-artifact@v4
  if: always()
  with:
    name: playwright-report
    path: playwright-report/
    retention-days: 30
```

## Visual Regression Testing

### Basic Screenshot Comparison

```typescript
test('homepage visual regression', async ({ page }) => {
  await page.goto('/');
  await expect(page).toHaveScreenshot('homepage.png');
});

// With options
test('component visual regression', async ({ page }) => {
  await page.goto('/components/button');
  const button = page.getByRole('button', { name: 'Submit' });
  await expect(button).toHaveScreenshot('submit-button.png', {
    maxDiffPixels: 100,
  });
});
```

### Update Snapshots

```bash
# Update all snapshots
npx playwright test --update-snapshots

# Update specific test snapshots
npx playwright test tests/visual.spec.ts --update-snapshots
```

## Debugging

### Debug Mode

```bash
# Step through test
npx playwright test --debug

# Debug specific test
npx playwright test tests/auth.spec.ts:10 --debug
```

### Trace Viewer

```typescript
// Enable trace in config
use: {
  trace: 'on-first-retry',  // or 'on', 'retain-on-failure'
}

// View trace after failure
npx playwright show-trace test-results/*/trace.zip
```

### Console Logging

```typescript
test('debug with console', async ({ page }) => {
  // Log page console messages
  page.on('console', msg => console.log('PAGE LOG:', msg.text()));

  // Log network requests
  page.on('request', req => console.log('REQUEST:', req.url()));

  await page.goto('/');
});
```

### Pause Execution

```typescript
test('debug with pause', async ({ page }) => {
  await page.goto('/');
  await page.pause(); // Opens inspector
  await page.getByRole('button').click();
});
```

## Best Practices

### 1. Use Accessible Selectors

```typescript
// Good - accessible and stable
page.getByRole('button', { name: 'Submit' })
page.getByLabel('Email address')
page.getByText('Welcome back')
page.getByTestId('user-profile')

// Avoid - fragile selectors
page.locator('.btn-primary')
page.locator('#submit-button')
page.locator('div > span > button')
```

### 2. Wait for Stability

```typescript
// Good - explicit waits
await page.getByRole('button').click();
await expect(page).toHaveURL('/dashboard');

// Or wait for specific element
await page.waitForSelector('[data-loaded="true"]');
```

### 3. Isolate Tests

```typescript
// Each test should be independent
test.beforeEach(async ({ page }) => {
  // Reset state before each test
  await page.goto('/');
});
```

### 4. Use Test Data Wisely

```typescript
// Use unique data per test run
const uniqueEmail = `test-${Date.now()}@example.com`;

// Clean up after tests
test.afterEach(async ({ request }) => {
  await request.delete('/api/test-data/cleanup');
});
```

### 5. Organize with Tags

```typescript
test('admin feature @admin', async ({ page }) => { /* ... */ });
test('checkout flow @smoke', async ({ page }) => { /* ... */ });

// Run tagged tests
// npx playwright test --grep @smoke
// npx playwright test --grep-invert @admin
```

## Troubleshooting

### Tests timing out

```typescript
// Increase timeout for slow operations
test('slow test', async ({ page }) => {
  test.setTimeout(60000); // 60 seconds
  await page.goto('/slow-page');
});

// Or in config
export default defineConfig({
  timeout: 60000,
  expect: { timeout: 10000 },
});
```

### Flaky tests

```typescript
// Add retries
export default defineConfig({
  retries: process.env.CI ? 2 : 0,
});

// Use web-first assertions (auto-retry)
await expect(page.getByText('Loaded')).toBeVisible();

// Avoid hard waits
// Bad: await page.waitForTimeout(1000);
// Good: await expect(element).toBeVisible();
```

### Browser not found

```bash
# Install browsers
npx playwright install

# Install with dependencies (Linux)
npx playwright install --with-deps

# Install specific browser
npx playwright install chromium
```

### Tests pass locally but fail in CI

1. Check environment differences
2. Ensure `webServer` command works in CI
3. Add trace for debugging: `trace: 'on'`
4. Check for timezone/locale differences
5. Verify network conditions (mock external APIs)

## Related Recipes

- `workflows/testing-instructions-writing.md` - Writing test documentation
- `testing/vitest.md` - Unit testing with Vitest
- `workflows/ci-cd.md` - CI/CD configuration
