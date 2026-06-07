// Obee Assistant side panel: a lean chat over POST /assistant/chat. Network and
// the JWT live in the background worker; this view only sends typed messages.
import { send } from "../lib/messages";

const thread = document.getElementById("thread") as HTMLElement;
const composer = document.getElementById("composer") as HTMLFormElement;
const input = document.getElementById("input") as HTMLTextAreaElement;
const sendBtn = document.getElementById("send") as HTMLButtonElement;
const modelBadge = document.getElementById("model") as HTMLElement;

let sessionId: string | undefined;

function bubble(text: string, kind: "user" | "bot", pending = false): HTMLElement {
  const node = document.createElement("div");
  node.className = `msg ${kind}${pending ? " pending" : ""}`;
  node.textContent = text;
  thread.append(node);
  thread.scrollTop = thread.scrollHeight;
  return node;
}

function notice(text: string): void {
  thread.replaceChildren(
    Object.assign(document.createElement("p"), { className: "muted", textContent: text }),
  );
}

async function init(): Promise<void> {
  try {
    const auth = await send({ type: "auth.status" });
    if (!auth.authenticated) {
      notice("Sign in from the Obee popup first, then reopen this panel.");
      return;
    }
    const status = await send({ type: "assistant.status" });
    modelBadge.textContent = status.model || status.provider;
    if (!status.enabled || !status.available) {
      notice(
        `Assistant unavailable (provider: ${status.provider}). ` +
          `Check ASSISTANT_ENABLED and the provider configuration on the API.`,
      );
      return;
    }
    thread.replaceChildren();
    bubble("Hi! Ask me about coffee, markets or sourcing.", "bot");
    composer.hidden = false;
    input.focus();
  } catch (err) {
    notice(message(err));
  }
}

composer.addEventListener("submit", async (e) => {
  e.preventDefault();
  const text = input.value.trim();
  if (!text) return;
  input.value = "";
  sendBtn.disabled = true;
  bubble(text, "user");
  const pending = bubble("…", "bot", true);
  try {
    const answer = await send({ type: "assistant.ask", message: text, sessionId });
    sessionId = answer.sessionId ?? sessionId;
    pending.classList.remove("pending");
    pending.textContent = answer.text || "(no answer)";
    if (answer.sources.length > 0) {
      const src = document.createElement("div");
      src.className = "sources";
      src.textContent = `Sources: ${answer.sources.join(", ")}`;
      thread.append(src);
    }
  } catch (err) {
    pending.classList.remove("pending");
    pending.classList.add("user");
    pending.textContent = message(err);
  } finally {
    sendBtn.disabled = false;
    thread.scrollTop = thread.scrollHeight;
    input.focus();
  }
});

// Submit on Enter (Shift+Enter inserts a newline).
input.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    composer.requestSubmit();
  }
});

function message(err: unknown): string {
  return err instanceof Error ? err.message : String(err);
}

void init();
