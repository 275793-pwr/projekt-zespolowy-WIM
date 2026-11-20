import React, { useState } from "react";
import { api } from "./api.js";

function Sources({ sources }) {
  return (
    <aside className="sources"><h3>Źródła</h3>
      {sources.length === 0 && <p className="muted">Brak źródeł.</p>}
      {sources.map((s, i) => (
        <div className="card" key={i}>
          <b>[{i + 1}] {s.document_title}</b>
          <div className="muted">{s.chapter && `${s.chapter}, `}strona {s.page}</div>
          <blockquote>{s.excerpt}</blockquote>
        </div>
      ))}
    </aside>
  );
}

export default function Chat() {
  const [q, setQ] = useState(""); const [state, setState] = useState({ kind: "idle" });
  const [convId, setConvId] = useState(null);
  const ask = async (e) => {
    e.preventDefault(); if (!q.trim()) return;
    setState({ kind: "loading" });
    try {
      const d = await api("/ask/", { method: "POST", json: { question: q, ...(convId && { conversation_id: convId }) } });
      if (d.conversation_id) setConvId(d.conversation_id);
      setState({ kind: d.status, data: d });
    } catch (x) { setState({ kind: "error", data: { answer: x.message || "Błąd serwera.", sources: [] } }); }
  };
  const d = state.data;
  return (
    <main className="chat">
      <section>
        <form onSubmit={ask}>
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Zadaj pytanie o dokumenty uczelniane…" maxLength={2000} />
          <button disabled={state.kind === "loading"}>Zapytaj</button>
        </form>
        {state.kind === "loading" && <div className="box loading" aria-busy="true">Szukam w dokumentach…</div>}
        {state.kind === "answered" && <div className="box answer">{d.answer}</div>}
        {state.kind === "refused" && <div className="box refused"><b>Brak odpowiedzi w dokumentach.</b><br />{d.answer}</div>}
        {state.kind === "error" && <div className="box err" role="alert"><b>Błąd.</b> {d.answer}</div>}
      </section>
      <Sources sources={d?.sources || []} />
    </main>
  );
}
