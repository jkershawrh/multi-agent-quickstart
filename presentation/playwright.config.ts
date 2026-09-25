import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: './visual-tests',
  expect: { toHaveScreenshot: { maxDiffPixels: 10000 } },
  webServer: { command: 'npm run dev -- --host 127.0.0.1', url: 'http://127.0.0.1:5173', reuseExistingServer: true },
  use: { baseURL: 'http://127.0.0.1:5173', colorScheme: 'dark', reducedMotion: 'reduce' },
  projects: [
    { name: 'stage-1080p', use: { viewport: { width: 1920, height: 1080 } } },
    { name: 'laptop', use: { viewport: { width: 1440, height: 900 } } },
    { name: 'rehearsal-mobile', use: { viewport: { width: 390, height: 844 } } },
  ],
})
