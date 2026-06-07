// Background service worker: owns the token, talks to the API, and drives
// on-demand page extraction. The popup communicates with it via messages.ts.
import {
  ApiError,
  assistantChat,
  assistantStatus,
  createCooperative,
  createRoaster,
  fetchMe,
  login,
} from "./lib/api";
import {
  clearToken,
  getBaseUrl,
  getToken,
  setBaseUrl,
  setLastEmail,
  setToken,
} from "./lib/auth";
import type { Request, Response } from "./lib/messages";
import type { AuthStatus, ExtractedPage } from "./lib/types";

/**
 * Injected into the active tab to read lightweight metadata. Must be fully
 * self-contained — it is serialized and runs in the page context, so it cannot
 * reference anything from this module.
 */
function extractPageData(): ExtractedPage {
  const meta = (name: string): string | undefined => {
    const el =
      document.querySelector(`meta[property="${name}"]`) ??
      document.querySelector(`meta[name="${name}"]`);
    const content = el?.getAttribute("content")?.trim();
    return content && content.length > 0 ? content : undefined;
  };

  const firstEmail = (): string | undefined => {
    const mailto = document.querySelector('a[href^="mailto:"]');
    const fromHref = mailto?.getAttribute("href")?.replace("mailto:", "").split("?")[0];
    if (fromHref) return fromHref.trim();
    const match = document.body?.innerText?.match(
      /[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}/i,
    );
    return match?.[0];
  };

  const name =
    meta("og:site_name") ??
    document.querySelector("h1")?.textContent?.trim() ??
    document.title.trim();

  const canonical = document
    .querySelector('link[rel="canonical"]')
    ?.getAttribute("href");

  return {
    title: document.title,
    sourceUrl: location.href,
    name: name && name.length > 0 ? name : undefined,
    website: canonical ?? location.origin,
    contactEmail: firstEmail(),
    description: meta("og:description") ?? meta("description"),
  };
}

async function buildAuthStatus(): Promise<AuthStatus> {
  const baseUrl = await getBaseUrl();
  const token = await getToken();
  if (!token) return { authenticated: false, baseUrl };
  try {
    const user = await fetchMe(baseUrl, token);
    return { authenticated: true, user, baseUrl };
  } catch (err) {
    if (err instanceof ApiError && err.status === 401) {
      await clearToken();
    }
    return { authenticated: false, baseUrl };
  }
}

async function getActiveTabId(): Promise<number> {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab?.id) throw new Error("No active tab");
  return tab.id;
}

async function handle(message: Request): Promise<unknown> {
  switch (message.type) {
    case "auth.status":
      return buildAuthStatus();

    case "auth.login": {
      const baseUrl = await getBaseUrl();
      const token = await login(baseUrl, message.email, message.password);
      await setToken(token);
      await setLastEmail(message.email);
      return buildAuthStatus();
    }

    case "auth.logout":
      await clearToken();
      return { done: true };

    case "config.setBaseUrl":
      await setBaseUrl(message.baseUrl);
      return buildAuthStatus();

    case "page.extract": {
      const tabId = await getActiveTabId();
      const [result] = await chrome.scripting.executeScript({
        target: { tabId },
        func: extractPageData,
      });
      if (!result?.result) throw new Error("Could not read this page");
      return result.result as ExtractedPage;
    }

    case "entity.create": {
      const baseUrl = await getBaseUrl();
      const token = await getToken();
      if (!token) throw new Error("Not signed in");
      return message.entityType === "roaster"
        ? createRoaster(baseUrl, token, message.draft)
        : createCooperative(baseUrl, token, message.draft);
    }

    case "assistant.status": {
      const baseUrl = await getBaseUrl();
      const token = await getToken();
      if (!token) throw new Error("Not signed in");
      return assistantStatus(baseUrl, token);
    }

    case "assistant.ask": {
      const baseUrl = await getBaseUrl();
      const token = await getToken();
      if (!token) throw new Error("Not signed in");
      return assistantChat(baseUrl, token, message.message, message.sessionId);
    }
  }
}

chrome.runtime.onMessage.addListener(
  (message: Request, _sender, sendResponse: (r: Response<unknown>) => void) => {
    handle(message)
      .then((data) => sendResponse({ ok: true, data }))
      .catch((err: unknown) =>
        sendResponse({ ok: false, error: err instanceof Error ? err.message : String(err) }),
      );
    return true; // keep the message channel open for the async response
  },
);
