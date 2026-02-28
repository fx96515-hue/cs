import { test, expect } from "@playwright/test";

const email = process.env.PLAYWRIGHT_EMAIL || "admin@coffeestudio.com";
const password = process.env.PLAYWRIGHT_PASSWORD || "AdminAdmin123!";

test("login redirects to dashboard", async ({ page }) => {
  await page.goto("/login", { waitUntil: "domcontentloaded" });
  await page.fill('input[autocomplete="email"]', email);
  await page.fill('input[type="password"]', password);
  const [loginResponse] = await Promise.all([
    page.waitForResponse(
      (res) =>
        res.url().includes("/auth/login") && res.request().method() === "POST"
    ),
    page.click('button[type="submit"]'),
  ]);
  expect(loginResponse.ok()).toBeTruthy();
  await page.waitForURL("**/dashboard", { timeout: 30_000 });
  await expect(page).toHaveURL(/\/dashboard/);
});
