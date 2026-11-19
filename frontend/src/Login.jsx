import React, { useState } from "react";
import { api } from "./api.js";

export default function Login({ onLogin }) {
  const [email, setEmail] = useState(""); const [password, setPassword] = useState("");
  const [err, setErr] = useState(""); const [busy, setBusy] = useState(false);
  const submit = async (e) => {
    e.preventDefault(); setBusy(true); setErr("");
    try { onLogin(await api("/auth/login/", { method: "POST", json: { email, password } })); }
    catch (x) { setErr(x.status === 401 ? "Nieprawidłowy e-mail lub hasło." : x.message); }
    setBusy(false);
  };
  return (
    <form className="login" onSubmit={submit}>
      <h1>Zaloguj się</h1>
      <input type="email" placeholder="E-mail" value={email} onChange={(e) => setEmail(e.target.value)} required />
      <input type="password" placeholder="Hasło" value={password} onChange={(e) => setPassword(e.target.value)} required />
      {err && <p className="error" role="alert">{err}</p>}
      <button disabled={busy}>{busy ? "Logowanie…" : "Zaloguj"}</button>
    </form>
  );
}
