import React, { useEffect, useState } from "react";
import { api, session, setUnauthorizedHandler } from "./api.js";
import Login from "./Login.jsx";
import Chat from "./Chat.jsx";
import Upload from "./Upload.jsx";

export default function App() {
  const [role, setRole] = useState(session.token ? session.role : null);
  const isAdmin = role === "corpus_admin";

  const login = (data) => {
    session.set(data);
    setRole(data.role);
  };
  const logout = () => {
    session.clear();
    setRole(null);
  };

  useEffect(() => { setUnauthorizedHandler(logout); }, []);
  useEffect(() => {
    if (session.token) api("/me/").then((me) => setRole(me.role)).catch(() => {});
  }, []);

  if (!role) return <Login onLogin={login} />;
  return (
    <div className="app">
      <header>
        <b>Asystent RAG do dokumentów uczelnianych</b>
        <span>{isAdmin ? "Administrator korpusu" : "Student"}</span>
        <button onClick={logout}>Wyloguj</button>
      </header>
      {isAdmin && <Upload />}
      <Chat />
    </div>
  );
}
