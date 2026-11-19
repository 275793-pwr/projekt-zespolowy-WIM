import { mockRequest } from "./mock.js";
const USE_MOCK = import.meta.env.VITE_USE_MOCK === "true";

export class ApiError extends Error {
  constructor(status, data) { super(data?.detail || `HTTP ${status}`); this.status = status; this.data = data; }
}
let onUnauthorized = () => {};
export const setUnauthorizedHandler = (fn) => (onUnauthorized = fn);

export const session = {
  get token() { return localStorage.getItem("access"); },
  set(d) { localStorage.setItem("access", d.access); localStorage.setItem("role", d.role); },
  clear() { localStorage.removeItem("access"); localStorage.removeItem("role"); },
};

export async function api(path, { method = "GET", json, form } = {}) {
  if (USE_MOCK) return mockRequest(path, { method, body: json ? JSON.stringify(json) : undefined });
  const headers = {};
  if (session.token) headers.Authorization = `Bearer ${session.token}`;
  if (json) headers["Content-Type"] = "application/json";
  let res;
  try {
    res = await fetch("/api" + path, { method, headers, body: json ? JSON.stringify(json) : form });
  } catch {
    throw new ApiError(0, { detail: "Brak połączenia z serwerem." });
  }
  const data = await res.json().catch(() => null);
  if (res.status === 401 && path !== "/auth/login/") { onUnauthorized(); }
  if (!res.ok) throw new ApiError(res.status, data);
  return data;
}
