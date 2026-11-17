import { ApiError } from "./types";
import type {
  AuthToken,
  ChatResponse,
  HistoryPage,
  RetrievalResponse,
  UploadInput,
  UploadedDocument,
  User,
} from "./types";

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");
const REQUEST_TIMEOUT_MS = 300_000;

async function request<T>(
  path: string,
  options: RequestInit = {},
  token?: string,
): Promise<T> {
  const headers = new Headers(options.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (options.body instanceof URLSearchParams && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/x-www-form-urlencoded");
  } else if (
    options.body &&
    !(options.body instanceof FormData) &&
    !(options.body instanceof URLSearchParams) &&
    !headers.has("Content-Type")
  ) {
    headers.set("Content-Type", "application/json");
  }

  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  try {
    const response = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers,
      signal: controller.signal,
    });
    if (response.status === 204) return undefined as T;

    const text = await response.text();
    let body: unknown = null;
    try {
      body = text ? JSON.parse(text) : null;
    } catch {
      body = text;
    }

    if (!response.ok) {
      const detail =
        body && typeof body === "object" && "detail" in body
          ? (body as { detail?: unknown }).detail
          : null;
      const validationDetail = Array.isArray(detail)
        ? detail
            .map((item) =>
              item && typeof item === "object" && "msg" in item && typeof item.msg === "string"
                ? item.msg.replace(/^Value error,\s*/i, "")
                : "",
            )
            .filter(Boolean)
            .join("; ")
        : null;
      const message =
        typeof detail === "string"
          ? detail
          : response.status === 422 && validationDetail
            ? validationDetail
          : response.status === 429
            ? "Too many requests. Please wait a moment and try again."
            : `The request failed (${response.status}). Please try again.`;
      throw new ApiError(message, response.status);
    }
    return body as T;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new ApiError("This is taking longer than expected. Please try again.");
    }
    throw new ApiError("Could not reach the assistant. Check your connection and try again.");
  } finally {
    window.clearTimeout(timeout);
  }
}

export const api = {
  register(email: string, password: string): Promise<User> {
    return request<User>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
  },

  login(email: string, password: string): Promise<AuthToken> {
    return request<AuthToken>(
      "/auth/token",
      {
        method: "POST",
        body: new URLSearchParams({ username: email, password }),
      },
    );
  },

  me(token: string): Promise<User> {
    return request<User>("/auth/me", {}, token);
  },

  history(token: string): Promise<HistoryPage> {
    return request<HistoryPage>("/history?limit=20&offset=0", {}, token);
  },

  upload(input: UploadInput, token: string): Promise<UploadedDocument> {
    if (input.source === "url") {
      return request<UploadedDocument>(
        "/documents/import-url",
        {
          method: "POST",
          body: JSON.stringify({
            url: input.url,
            company: input.company,
            reporting_year: input.reportingYear,
            document_type: input.documentType,
          }),
        },
        token,
      );
    }
    const form = new FormData();
    form.set("file", input.file);
    form.set("company", input.company);
    form.set("document_type", input.documentType);
    if (input.reportingYear) form.set("reporting_year", String(input.reportingYear));
    return request<UploadedDocument>("/documents/upload", { method: "POST", body: form }, token);
  },

  chat(question: string, token: string): Promise<ChatResponse> {
    return request<ChatResponse>(
      "/chat",
      {
        method: "POST",
        body: JSON.stringify({ question, filters: {}, top_k: 5 }),
      },
      token,
    );
  },

  search(question: string, token: string): Promise<RetrievalResponse> {
    return request<RetrievalResponse>(
      "/retrieval/search",
      {
        method: "POST",
        body: JSON.stringify({ question, filters: {}, top_k: 5 }),
      },
      token,
    );
  },
};
