import { expect, Page, Route, test } from "@playwright/test";

type MockResponse = {
  status?: number;
  body: unknown;
};

const DEFAULT_API_RESPONSES: Record<string, MockResponse> = {
  "/health": { body: { status: "ok" } },
  "/market/latest": {
    body: {
      "FX:USD_EUR": {
        value: 0.9234,
        unit: null,
        currency: null,
        observed_at: "2026-03-12T09:00:00Z",
      },
      "COFFEE_C:USD_LB": {
        value: 2.77,
        unit: "lb",
        currency: "USD",
        observed_at: "2026-03-12T09:00:00Z",
      },
    },
  },
  "/cooperatives?limit=1": { body: { items: [{ id: 1 }], total: 17 } },
  "/roasters?limit=1": { body: { items: [{ id: 1 }], total: 8 } },
  "/news?limit=5": {
    body: [
      {
        id: 1,
        topic: "peru",
        title: "Peru harvest signal",
        source: "Coffee News",
        url: "https://example.com/news-1",
        published_at: "2026-03-12T08:30:00Z",
      },
    ],
  },
  "/reports?limit=5": {
    body: [
      {
        id: 1,
        name: "Daily ingest",
        kind: "pipeline",
        status: "ok",
        report_at: "2026-03-12T08:00:00Z",
      },
    ],
  },
  "/ops/overview": { body: { data_quality: { open_flags: 2, critical_flags: 1 } } },
  "/anomalies?acknowledged=false&limit=5": {
    body: [
      {
        id: 91,
        entity_type: "cooperative",
        entity_id: 12,
        alert_type: "score_anomaly",
        field_name: null,
        old_value: 0.62,
        new_value: 0.31,
        change_amount: -0.31,
        severity: "warning",
        acknowledged: false,
        created_at: "2026-03-12T06:00:00Z",
      },
    ],
  },
};

async function seedAuth(page: Page): Promise<void> {
  await page.addInitScript(() => {
    window.localStorage.setItem("token", "test-token");
  });
}

async function mockApi(
  page: Page,
  overrides: Record<string, MockResponse> = {}
): Promise<void> {
  const responses: Record<string, MockResponse> = {
    ...DEFAULT_API_RESPONSES,
    ...overrides,
  };

  const handler = async (route: Route) => {
    const reqUrl = new URL(route.request().url());
    const key = `${reqUrl.pathname}${reqUrl.search}`;
    const mock = responses[key] ?? responses[reqUrl.pathname];
    const status = mock?.status ?? 200;
    const body = mock?.body ?? { detail: "mock-not-found" };

    await route.fulfill({
      status: mock ? status : 404,
      contentType: "application/json",
      body: JSON.stringify(body),
    });
  };

  await page.route("http://localhost:8000/**", handler);
  await page.route("http://api.localhost/**", handler);
}

test("dashboard renders key production widgets", async ({ page }) => {
  await seedAuth(page);
  await mockApi(page);

  await page.goto("/dashboard", { waitUntil: "domcontentloaded" });

  await expect(page.locator(".pageHeader .h1")).toHaveText("Dashboard Übersicht");
  await expect(page.locator(".kpiGrid")).toContainText("Kooperativen");
  await expect(page.locator(".kpiGrid")).toContainText("Röstereien");
  await expect(page.locator(".kpiGrid")).toContainText("1 kritisch", {
    timeout: 15_000,
  });
  await expect(page.locator(".kpiGrid")).toContainText("Datenqualität");
  await expect(page.getByText("Peru harvest signal")).toBeVisible();
  await expect(page.getByText("Daily ingest")).toBeVisible();
  await expect(page.getByText("Anomalie-Feed")).toBeVisible();
});

test("dashboard shows sanitized load error when an API dependency fails", async ({
  page,
}) => {
  await seedAuth(page);
  await mockApi(page, {
    "/ops/overview": { status: 500, body: { detail: "internal boom" } },
  });

  await page.goto("/dashboard", { waitUntil: "domcontentloaded" });

  await expect(page.getByText("Fehler beim Laden")).toBeVisible({ timeout: 15_000 });
  await expect(page.getByText(/Serverfehler \(500\)/)).toBeVisible({ timeout: 15_000 });
});
