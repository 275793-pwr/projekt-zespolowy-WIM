import React, { useEffect, useState } from "react";
import { api } from "./api.js";

const STATUS_LABELS = { uploaded: "wgrany", processing: "przetwarzanie…", ready: "gotowy", failed: "błąd" };

export default function Upload() {
  const [documents, setDocuments] = useState([]);
  const [file, setFile] = useState(null);
  const [title, setTitle] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  const loadDocuments = () => api("/documents/").then(setDocuments).catch(() => {});
  useEffect(() => { loadDocuments(); }, []);

  async function remove(document) {
    if (!window.confirm(`Usunąć dokument „${document.title}”? Tej operacji nie można cofnąć.`)) return;
    try {
      await api(`/documents/${document.id}/`, { method: "DELETE" });
      setMessage(`Usunięto: ${document.title}`);
      loadDocuments();
    } catch (err) {
      setMessage(err.message);
    }
  }

  async function submit(event) {
    event.preventDefault();
    if (!file) return;
    setBusy(true);
    setMessage("");
    const form = new FormData();
    form.append("file", file);
    if (title) form.append("title", title);
    try {
      const created = await api("/documents/", { method: "POST", form });
      setMessage(created.status === "failed"
        ? `Indeksowanie nie powiodło się: ${created.failure_reason}`
        : `Status: ${STATUS_LABELS[created.status]}`);
      loadDocuments();
    } catch (err) {
      setMessage(err.data?.file?.[0] || err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="upload">
      <h3>Wgraj PDF (administrator)</h3>
      <form onSubmit={submit}>
        <input placeholder="Tytuł (opcjonalnie)" value={title} onChange={(e) => setTitle(e.target.value)} />
        <input type="file" accept="application/pdf" onChange={(e) => setFile(e.target.files[0])} />
        <button disabled={busy || !file}>{busy ? "Indeksowanie…" : "Wgraj"}</button>
      </form>
      {message && <p>{message}</p>}
      <ul>
        {documents.map((doc) => (
          <li key={doc.id}>
            {doc.title} — {STATUS_LABELS[doc.status]}
            {doc.status === "ready" && ` (${doc.page_count} str., ${doc.chunk_count} fragm.)`}
            {doc.failure_reason && ` — ${doc.failure_reason}`}{" "}
            <button className="danger" onClick={() => remove(doc)}>Usuń</button>
          </li>
        ))}
      </ul>
    </section>
  );
}
