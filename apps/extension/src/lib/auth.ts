// Token + configuration storage. The JWT lives in chrome.storage.session so it
// is cleared when the browser closes; non-secret config lives in local storage.
export const DEFAULT_BASE_URL = "http://localhost:8000";

const TOKEN_KEY = "obee.token";
const BASE_URL_KEY = "obee.baseUrl";
const LAST_EMAIL_KEY = "obee.lastEmail";

export async function getToken(): Promise<string | undefined> {
  const { [TOKEN_KEY]: token } = await chrome.storage.session.get(TOKEN_KEY);
  return typeof token === "string" ? token : undefined;
}

export async function setToken(token: string): Promise<void> {
  await chrome.storage.session.set({ [TOKEN_KEY]: token });
}

export async function clearToken(): Promise<void> {
  await chrome.storage.session.remove(TOKEN_KEY);
}

export async function getBaseUrl(): Promise<string> {
  const { [BASE_URL_KEY]: url } = await chrome.storage.local.get(BASE_URL_KEY);
  return typeof url === "string" && url.length > 0 ? url : DEFAULT_BASE_URL;
}

export async function setBaseUrl(url: string): Promise<void> {
  await chrome.storage.local.set({ [BASE_URL_KEY]: url.replace(/\/+$/, "") });
}

export async function getLastEmail(): Promise<string | undefined> {
  const { [LAST_EMAIL_KEY]: email } = await chrome.storage.local.get(LAST_EMAIL_KEY);
  return typeof email === "string" ? email : undefined;
}

export async function setLastEmail(email: string): Promise<void> {
  await chrome.storage.local.set({ [LAST_EMAIL_KEY]: email });
}
