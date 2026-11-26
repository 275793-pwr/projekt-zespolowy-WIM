import React, { useEffect, useState } from "react";
import { api } from "./api.js";

const dateFormat = new Intl.DateTimeFormat("pl-PL", { dateStyle: "medium" });

function Sources({ sources }) {
  if (!sources?.length) return null;
  return (
    <details className="sources">
      <summary>Źródła ({sources.length})</summary>
      {sources.map((source, index) => (
        <div className="card" key={index}>
          <b>[{index + 1}] {source.document_title}</b>
          <div className="muted">{source.chapter && `${source.chapter}, `}strona {source.page}</div>
          <blockquote>{source.excerpt}</blockquote>
        </div>
      ))}
    </details>
  );
}

const emptyThread = { id: null, messages: [] };

export default function Chat() {
  const [question, setQuestion] = useState("");
  const [thread, setThread] = useState(emptyThread);
  const [history, setHistory] = useState(null);
  const [historyError, setHistoryError] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState("");

  async function loadHistory() {
    setHistoryError("");
    try {
      setHistory(await api("/conversations/"));
    } catch (err) {
      setHistoryError(err.status === 404
        ? "Historia rozmów nie jest jeszcze dostępna."
        : "Nie udało się pobrać historii rozmów.");
    }
  }

  useEffect(() => { void loadHistory(); }, []);

  async function openThread(id) {
    setBusy("opening");
    setError("");
    try {
      setThread(await api(`/conversations/${encodeURIComponent(id)}/`));
      setQuestion("");
    } catch {
      setError("Nie udało się otworzyć rozmowy.");
    } finally {
      setBusy("");
    }
  }

  function startThread() {
    setThread(emptyThread);
    setQuestion("");
    setError("");
  }

  async function ask(event) {
    event.preventDefault();
    const content = question.trim();
    if (!content || busy) return;
    setBusy("asking");
    setError("");
    try {
      const result = await api("/ask/", {
        method: "POST",
        json: { question: content, ...(thread.id && { conversation_id: thread.id }) },
      });
      if (!result.conversation_id) {
        setError(result.answer || "Nie udało się wysłać pytania.");
        return;
      }
      setThread({
        id: result.conversation_id,
        messages: [...thread.messages,
          { role: "user", content },
          { id: result.message_id, role: "assistant", content: result.answer, status: result.status, sources: result.sources }],
      });
      setQuestion("");
      if (!historyError) void loadHistory();
    } catch {
      setError("Nie udało się wysłać pytania. Spróbuj ponownie.");
    } finally {
      setBusy("");
    }
  }

  return (
    <main className="chat">
      <aside className="chat-history" aria-label="Historia rozmów">
        <button type="button" disabled={!!busy} onClick={startThread}>Nowa rozmowa</button>
        <h2>Historia rozmów</h2>
        {!history && !historyError && <p className="muted" role="status">Wczytywanie historii…</p>}
        {historyError && <div><p className="muted" role="status">{historyError}</p>
          <button type="button" onClick={loadHistory}>Odśwież historię</button></div>}
        {history?.length === 0 && !historyError && <p className="muted">Brak zapisanych rozmów.</p>}
        <ul>
          {history?.map(item => (
            <li key={item.id}>
              <button type="button" aria-current={thread.id === item.id ? "true" : undefined}
                disabled={!!busy} onClick={() => openThread(item.id)}>
                <span>{item.title || "Rozmowa bez tytułu"}</span>
                <small>{dateFormat.format(new Date(item.updated_at))}</small>
              </button>
            </li>
          ))}
        </ul>
      </aside>
      <section className="chat-thread" aria-label="Rozmowa">
        {!thread.messages.length && <h2>Zadaj pytanie o dokumenty uczelniane</h2>}
        <div role="log" aria-label="Wiadomości">
          {thread.messages.map((message, index) => (
            <article className={`box ${message.role === "user" ? "user-message" : message.status === "error" ? "err" : message.status || ""}`}
              key={message.id ?? index}>
              <strong>{message.role === "user" ? "Ty" : "Asystent"}</strong>
              <p>{message.content}</p>
              <Sources sources={message.sources} />
            </article>
          ))}
        </div>
        {busy && <p className="muted" role="status">{busy === "asking" ? "Szukam w dokumentach…" : "Otwieram rozmowę…"}</p>}
        {error && <p className="error" role="alert">{error}</p>}
        <form onSubmit={ask}>
          <input aria-label="Pytanie" value={question} onChange={e => setQuestion(e.target.value)}
            placeholder="Wpisz pytanie…" maxLength={2000} disabled={!!busy} />
          <button disabled={!!busy || !question.trim()}>Zapytaj</button>
        </form>
      </section>
    </main>
  );
}
