const wait = ms => new Promise(resolve => setTimeout(resolve, ms));
const account = () => localStorage.getItem("mock-email") || "student@example.com";
const historyKey = () => "mock-conversations:" + account();

export async function mockRequest(path, opts = {}) {
  await wait(250);
  const body = opts.body ? JSON.parse(opts.body) : {};
  if (path === "/auth/login/") {
    const email = body.email.trim().toLowerCase();
    localStorage.setItem("mock-email", email);
    return { access: "mock", refresh: "mock", role: email.startsWith("admin") ? "corpus_admin" : "student" };
  }
  if (path === "/me/") return { email: account(), role: localStorage.getItem("role") || "student" };
  if (path === "/documents/" && opts.method === "POST") return { id: "mock-1", title: "Regulamin studiów", status: "ready" };
  if (path === "/documents/") return [];

  const threads = JSON.parse(localStorage.getItem(historyKey()) || "[]");
  if (path === "/conversations/") {
    return threads.map(({ id, title, updated_at }) => ({ id, title, updated_at }));
  }
  const match = path.match(/^\/conversations\/([^/]+)\/$/);
  if (match) {
    const thread = threads.find(item => item.id === match[1]);
    if (!thread) throw Object.assign(new Error("Nie znaleziono rozmowy."), { status: 404 });
    return thread;
  }
  if (path === "/ask/") {
    const existing = threads.find(item => item.id === body.conversation_id);
    const thread = existing || { id: crypto.randomUUID(), title: body.question.slice(0, 80), messages: [] };
    const question = body.question.toLowerCase();
    const result = { message_id: crypto.randomUUID(), conversation_id: thread.id,
      status: "answered", answer: "Za semestr można uzyskać 30 punktów ECTS [1].",
      sources: [{ document_title: "Regulamin studiów", page: 3, chapter: "§ 9", excerpt: "Za semestr studiów student może uzyskać 30 punktów ECTS..." }] };
    if (question.includes("błąd")) {
      Object.assign(result, { status: "error", answer: "Usługa odpowiedzi jest chwilowo niedostępna.", sources: [] });
    } else if (question.includes("żurek")) {
      Object.assign(result, { status: "refused", answer: "Nie znalazłem tego w dokumentach.", sources: [] });
    }
    thread.messages.push(
      { id: crypto.randomUUID(), role: "user", content: body.question },
      { id: result.message_id, role: "assistant", content: result.answer, status: result.status, sources: result.sources },
    );
    thread.updated_at = new Date().toISOString();
    localStorage.setItem(historyKey(), JSON.stringify([thread, ...threads.filter(item => item.id !== thread.id)]));
    return result;
  }
  throw new Error("mock: " + path);
}
