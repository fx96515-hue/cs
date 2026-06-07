// Popup UI (vanilla TS). All network/auth work is delegated to the background
// worker via the typed `send` helper. DOM is built with createElement +
// textContent so clipped page content is never interpolated as HTML.
import { send } from "../lib/messages";
import type { AuthStatus, ExtractedPage, RoasterDraft } from "../lib/types";

const app = document.getElementById("app") as HTMLElement;
const userBadge = document.getElementById("user") as HTMLElement;
const versionEl = document.getElementById("version") as HTMLElement;
const settingsToggle = document.getElementById("settings-toggle") as HTMLButtonElement;

let showSettings = false;

function el<K extends keyof HTMLElementTagNameMap>(
  tag: K,
  props: Partial<HTMLElementTagNameMap[K]> = {},
  children: (Node | string)[] = [],
): HTMLElementTagNameMap[K] {
  const node = Object.assign(document.createElement(tag), props);
  for (const c of children) node.append(typeof c === "string" ? document.createTextNode(c) : c);
  return node;
}

function field(label: string, input: HTMLElement): HTMLElement {
  return el("div", {}, [el("label", { textContent: label }), input]);
}

function statusLine(text: string, kind: "ok" | "err"): HTMLElement {
  return el("div", { className: `status ${kind}`, textContent: text });
}

function setBadge(status: AuthStatus): void {
  if (status.authenticated && status.user) {
    userBadge.textContent = status.user.email;
    userBadge.hidden = false;
  } else {
    userBadge.hidden = true;
  }
}

async function refresh(): Promise<void> {
  app.replaceChildren(el("p", { className: "muted", textContent: "Loading…" }));
  try {
    const status = await send({ type: "auth.status" });
    setBadge(status);
    if (showSettings) renderSettings(status);
    else if (status.authenticated) renderClip(status);
    else renderLogin(status);
  } catch (err) {
    app.replaceChildren(statusLine(message(err), "err"));
  }
}

function renderLogin(status: AuthStatus): void {
  const email = el("input", { type: "email", placeholder: "you@example.com", autofocus: true });
  const password = el("input", { type: "password", placeholder: "Password" });
  const submit = el("button", { className: "primary", textContent: "Sign in" });
  const form = el("form", {}, [
    el("h2", { textContent: "Sign in to CoffeeStudio" }),
    field("Email", email),
    field("Password", password),
    submit,
    el("p", { className: "source", textContent: `API: ${status.baseUrl}` }),
  ]);

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    submit.disabled = true;
    try {
      const next = await send({ type: "auth.login", email: email.value, password: password.value });
      setBadge(next);
      renderClip(next);
    } catch (err) {
      form.append(statusLine(message(err), "err"));
      submit.disabled = false;
    }
  });

  app.replaceChildren(form);
}

function renderClip(_status: AuthStatus): void {
  const readBtn = el("button", { className: "primary", textContent: "Read this page" });
  const container = el("div", {}, [
    el("h2", { textContent: "Clip a roaster" }),
    el("p", { className: "muted", textContent: "Pull details from the current tab, review, then save." }),
    readBtn,
  ]);

  readBtn.addEventListener("click", async () => {
    readBtn.disabled = true;
    readBtn.textContent = "Reading…";
    try {
      const page = await send({ type: "page.extract" });
      renderForm(page);
    } catch (err) {
      container.append(statusLine(message(err), "err"));
      readBtn.disabled = false;
      readBtn.textContent = "Read this page";
    }
  });

  app.replaceChildren(container);
}

function renderForm(page: ExtractedPage): void {
  const name = el("input", { type: "text", value: page.name ?? "" });
  const website = el("input", { type: "url", value: page.website ?? "" });
  const city = el("input", { type: "text", value: "" });
  const email = el("input", { type: "email", value: page.contactEmail ?? "" });
  const peru = el("input", { type: "checkbox" });
  const notes = el("textarea", { value: page.description ?? "" });
  const save = el("button", { className: "primary", textContent: "Save to CoffeeStudio" });

  const form = el("form", {}, [
    el("h2", { textContent: "Review & save" }),
    field("Name *", name),
    field("Website", website),
    field("City", city),
    field("Contact email", email),
    el("label", { className: "row check" }, [peru, el("span", { textContent: " Peru focus" })]),
    field("Notes", notes),
    save,
    el("p", { className: "source", textContent: page.sourceUrl }),
  ]);

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (name.value.trim().length < 2) {
      form.append(statusLine("Name must be at least 2 characters.", "err"));
      return;
    }
    save.disabled = true;
    const draft: RoasterDraft = {
      name: name.value.trim(),
      website: website.value.trim() || undefined,
      city: city.value.trim() || undefined,
      contact_email: email.value.trim() || undefined,
      peru_focus: peru.checked,
      notes: notes.value.trim() || undefined,
      meta: { source: "obee", source_url: page.sourceUrl, page_title: page.title },
    };
    try {
      const created = await send({ type: "roaster.create", draft });
      app.replaceChildren(
        statusLine(`Saved “${created.name}” (#${created.id}).`, "ok"),
        el("button", { className: "primary", textContent: "Clip another", onclick: refresh }),
      );
    } catch (err) {
      form.append(statusLine(message(err), "err"));
      save.disabled = false;
    }
  });

  app.replaceChildren(form);
}

function renderSettings(status: AuthStatus): void {
  const base = el("input", { type: "url", value: status.baseUrl });
  const save = el("button", { className: "primary", textContent: "Save" });
  const form = el("form", {}, [el("h2", { textContent: "Settings" }), field("API base URL", base), save]);

  save.addEventListener("click", async (e) => {
    e.preventDefault();
    try {
      await send({ type: "config.setBaseUrl", baseUrl: base.value.trim() });
      showSettings = false;
      await refresh();
    } catch (err) {
      form.append(statusLine(message(err), "err"));
    }
  });

  if (status.authenticated) {
    const signOut = el("button", { className: "link", textContent: "Sign out" });
    signOut.style.marginTop = "10px";
    signOut.addEventListener("click", async (e) => {
      e.preventDefault();
      await send({ type: "auth.logout" });
      showSettings = false;
      await refresh();
    });
    form.append(signOut);
  }

  app.replaceChildren(form);
}

function message(err: unknown): string {
  return err instanceof Error ? err.message : String(err);
}

settingsToggle.addEventListener("click", () => {
  showSettings = !showSettings;
  void refresh();
});

versionEl.textContent = `v${chrome.runtime.getManifest().version}`;
void refresh();
