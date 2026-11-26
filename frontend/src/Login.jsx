import React, { useState } from "react";
import { api } from "./api.js";

export default function Login({ onLogin }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      onLogin(await api("/auth/login/", { method: "POST", json: { email, password } }));
    } catch (err) {
      setError(err.status === 401 ? "Nieprawidłowy e-mail lub hasło." : err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="login" onSubmit={submit}>
      <h1>Zaloguj się</h1>
      <input type="email" placeholder="E-mail" value={email} onChange={(e) => setEmail(e.target.value)} required />
      <input type="password" placeholder="Hasło" value={password} onChange={(e) => setPassword(e.target.value)} required />
      {error && <p className="error" role="alert">{error}</p>}
      <button disabled={busy}>{busy ? "Logowanie…" : "Zaloguj"}</button>
    </form>
  );
}
