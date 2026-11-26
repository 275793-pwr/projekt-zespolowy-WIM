// Atrapa backendu w formacie kontraktu (sekcja 8). Włączana przez VITE_USE_MOCK=true.
const wait = (ms) => new Promise((r) => setTimeout(r, ms));
export async function mockRequest(path, opts = {}) {
  await wait(500);
  const body = opts.body && typeof opts.body === "string" ? JSON.parse(opts.body) : {};
  if (path === "/auth/login/") return { access: "mock", refresh: "mock", role: body.email?.startsWith("admin") ? "corpus_admin" : "student" };
  if (path === "/me/") return { email: "mock@example.com", role: localStorage.getItem("role") || "student" };
  if (path === "/documents/" && opts.method === "POST") return { id: "mock-1", title: "Regulamin studiów", status: "ready" };
  if (path.startsWith("/documents/") && opts.method === "DELETE") return null;
  if (path === "/documents/") return [];
  if (path === "/ask/") {
    const q = (body.question || "").toLowerCase();
    if (q.includes("błąd")) return { message_id: null, status: "error", answer: "Usługa odpowiedzi jest chwilowo niedostępna.", sources: [] };
    if (q.includes("żurek")) return { message_id: "m", status: "refused", answer: "Nie znalazłem tego w dokumentach.", sources: [] };
    return { message_id: "m", status: "answered", answer: "Za semestr można uzyskać 30 punktów ECTS [1].",
      sources: [{ document_title: "Regulamin studiów", page: 3, chapter: "§ 9", excerpt: "Za semestr studiów student może uzyskać 30 punktów ECTS..." }] };
  }
  throw new Error("mock: " + path);
}
