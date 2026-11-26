import { mockRequest } from "./mock.js";

const USE_MOCK = import.meta.env.VITE_USE_MOCK === "true";

class ApiError extends Error {
  constructor(status, data) {
    super(data?.detail || `HTTP ${status}`);
    this.status = status;
    this.data = data;
  }
}

let onUnauthorized = () => {};
export const setUnauthorizedHandler = (handler) => {
  onUnauthorized = handler;
};

export const session = {
  get token() {
    return localStorage.getItem("access");
  },
  get role() {
    return localStorage.getItem("role");
  },
  set({ access, role }) {
    localStorage.setItem("access", access);
    localStorage.setItem("role", role);
  },
  clear() {
    localStorage.removeItem("access");
    localStorage.removeItem("role");
  },
};

export async function api(path, { method = "GET", json, form } = {}) {
  const jsonBody = json ? JSON.stringify(json) : undefined;
  if (USE_MOCK) return mockRequest(path, { method, body: jsonBody });

  const headers = {};
  if (session.token) headers.Authorization = `Bearer ${session.token}`;
  if (json) headers["Content-Type"] = "application/json";

  let response;
  try {
    response = await fetch("/api" + path, { method, headers, body: jsonBody ?? form });
  } catch {
    throw new ApiError(0, { detail: "Brak połączenia z serwerem." });
  }
  const data = await response.json().catch(() => null);
  if (response.status === 401 && path !== "/auth/login/") onUnauthorized();
  if (!response.ok) throw new ApiError(response.status, data);
  return data;
}
