import React, { useEffect, useState } from "react";
import { api } from "./api.js";

const LABEL = { uploaded: "wgrany", processing: "przetwarzanie…", ready: "gotowy", failed: "błąd" };

export default function Upload() {
  const [docs, setDocs] = useState([]); const [file, setFile] = useState(null);
  const [title, setTitle] = useState(""); const [msg, setMsg] = useState(""); const [busy, setBusy] = useState(false);
  const load = () => api("/documents/").then(setDocs).catch(() => {});
  useEffect(() => { load(); }, []);
  const submit = async (e) => {
    e.preventDefault(); if (!file) return;
    setBusy(true); setMsg("");
    const form = new FormData(); form.append("file", file); if (title) form.append("title", title);
    try {
      const d = await api("/documents/", { method: "POST", form });
      setMsg(d.status === "failed" ? `Indeksowanie nie powiodło się: ${d.failure_reason}` : `Status: ${LABEL[d.status]}`);
      load();
    } catch (x) { setMsg(x.data?.file?.[0] || x.message); }
    setBusy(false);
  };
  return (
    <section className="upload"><h3>Wgraj PDF (administrator)</h3>
      <form onSubmit={submit}>
        <input placeholder="Tytuł (opcjonalnie)" value={title} onChange={(e) => setTitle(e.target.value)} />
        <input type="file" accept="application/pdf" onChange={(e) => setFile(e.target.files[0])} />
        <button disabled={busy || !file}>{busy ? "Indeksowanie…" : "Wgraj"}</button>
      </form>
      {msg && <p>{msg}</p>}
      <ul>{docs.map((d) => <li key={d.id}>{d.title} — {LABEL[d.status]}{d.status === "ready" && ` (${d.page_count} str., ${d.chunk_count} fragm.)`}{d.failure_reason && ` — ${d.failure_reason}`}</li>)}</ul>
    </section>
  );
}
