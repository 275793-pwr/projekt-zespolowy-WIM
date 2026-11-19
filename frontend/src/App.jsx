import React, { useEffect, useState } from "react";
import { api, session, setUnauthorizedHandler } from "./api.js";
import Login from "./Login.jsx";
import Chat from "./Chat.jsx";
import Upload from "./Upload.jsx";

export default function App() {
  const [role, setRole] = useState(session.token ? localStorage.getItem("role") : null);
  const logout = () => { session.clear(); setRole(null); };
  useEffect(() => setUnauthorizedHandler(logout), []);
  useEffect(() => { if (session.token) api("/me/").then((m) => setRole(m.role)).catch(() => {}); }, []);

  if (!role) return <Login onLogin={(d) => { session.set(d); setRole(d.role); }} />;
  return (
    <div className="app">
      <header><b>Asystent regulaminów</b><span>{role === "corpus_admin" ? "Administrator korpusu" : "Student"}</span>
        <button onClick={logout}>Wyloguj</button></header>
      {role === "corpus_admin" && <Upload />}
      <Chat />
    </div>
  );
}
