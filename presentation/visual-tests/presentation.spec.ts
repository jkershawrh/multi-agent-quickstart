import { expect, test } from '@playwright/test'

test('opening and architecture remain visually stable', async ({ page }) => {
  await page.goto('/')
  await expect(page).toHaveScreenshot('opening.png', { fullPage: true })
  await page.goto('/?act=1&scene=0')
  await expect(page).toHaveScreenshot('architecture.png', { fullPage: true })
})

test('live journey opens as a workload workspace with topology on demand', async ({ page }) => {
  await page.goto('/?act=2&scene=0')
  await expect(page.getByText('Investigate INC-1042 and prepare—but do not execute—a remediation.')).toBeVisible()
  await expect(page.getByRole('button', { name: 'Inspect the authority boundary' })).toBeVisible()
  await expect(page).toHaveScreenshot('live-journey.png', { fullPage: true })
})

test('core controls are keyboard reachable', async ({ page }) => {
  await page.goto('/?act=0&scene=0')
  await page.keyboard.press('Tab')
  await expect(page.getByRole('button', { name: 'Restart presentation' })).toBeFocused()
})
