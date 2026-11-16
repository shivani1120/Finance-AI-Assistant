import { useCallback, useEffect, useRef, useState } from "react";
import { Menu, Plus, ShieldCheck, UploadCloud } from "lucide-react";
import { api } from "./api/client";
import { ApiError } from "./api/types";
import type { ChatMessageData, ChatSource, HistoryEntry, UploadInput, User } from "./api/types";
import { AppSidebar } from "./components/AppSidebar";
import { AuthScreen } from "./components/AuthScreen";
import { ChatComposer, type QuestionMode } from "./components/ChatComposer";
import { ChatMessage } from "./components/ChatMessage";
import { UploadDialog } from "./components/UploadDialog";
import { WelcomePanel } from "./components/WelcomePanel";

const TOKEN_KEY = "finance_ai_access_token";

function newId() {
  return crypto.randomUUID();
}

function asApiError(error: unknown) {
  return error instanceof ApiError ? error : new ApiError("Something went wrong. Please try again.");
}

export default function App() {
  const [token, setToken] = useState<string | null>(() => sessionStorage.getItem(TOKEN_KEY));
  const [user, setUser] = useState<User | null>(null);
  const [authLoading, setAuthLoading] = useState(Boolean(sessionStorage.getItem(TOKEN_KEY)));
  const [authBusy, setAuthBusy] = useState(false);
  const [authError, setAuthError] = useState("");
  const [authNotice, setAuthNotice] = useState("");
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [activeHistoryId, setActiveHistoryId] = useState<number | null>(null);
  const [messages, setMessages] = useState<ChatMessageData[]>([]);
  const [mode, setMode] = useState<QuestionMode>("chat");
  const [busy, setBusy] = useState(false);
  const [requestError, setRequestError] = useState("");
  const [failedRequest, setFailedRequest] = useState<{ question: string; mode: QuestionMode } | null>(null);
  const [uploadOpen, setUploadOpen] = useState(false);
  const [uploadBusy, setUploadBusy] = useState(false);
  const [uploadError, setUploadError] = useState("");
  const [uploadSummary, setUploadSummary] = useState<string | null>(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [toast, setToast] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  const signOut = useCallback((notice?: string) => {
    sessionStorage.removeItem(TOKEN_KEY);
    setToken(null);
    setUser(null);
    setHistory([]);
    setMessages([]);
    setActiveHistoryId(null);
    setAuthError(notice ?? "");
    setAuthNotice("");
  }, []);

  const refreshHistory = useCallback(async (accessToken: string) => {
    try {
      const result = await api.history(accessToken);
      setHistory(result.items);
    } catch (error) {
      const apiError = asApiError(error);
      if (apiError.status === 401) signOut("Your session expired. Please sign in again.");
    }
  }, [signOut]);

  useEffect(() => {
    if (!token) {
      setAuthLoading(false);
      return;
    }
    let cancelled = false;
    setAuthLoading(true);
    Promise.all([api.me(token), api.history(token)])
      .then(([profile, historyPage]) => {
        if (cancelled) return;
        setUser(profile);
        setHistory(historyPage.items);
      })
      .catch((error: unknown) => {
        if (cancelled) return;
        const apiError = asApiError(error);
        if (apiError.status === 401) signOut("Your session expired. Please sign in again.");
        else setAuthError(apiError.message);
      })
      .finally(() => {
        if (!cancelled) setAuthLoading(false);
      });
    return () => { cancelled = true; };
  }, [token, signOut]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, busy]);

  async function handleAuth(mode: "login" | "register", email: string, password: string) {
    setAuthBusy(true);
    setAuthError("");
    setAuthNotice("");
    try {
      if (mode === "register") {
        await api.register(email, password);
        setAuthNotice("Account created. Sign in with your email and password.");
        return "registered" as const;
      }
      const response = await api.login(email, password);
      sessionStorage.setItem(TOKEN_KEY, response.access_token);
      setAuthNotice("");
      setToken(response.access_token);
      return "signed-in" as const;
    } catch (error) {
      setAuthError(asApiError(error).message);
      return undefined;
    } finally {
      setAuthBusy(false);
    }
  }

  async function handleUpload(input: UploadInput) {
    if (!token) return;
    setUploadBusy(true);
    setUploadError("");
    try {
      const uploaded = await api.upload(input, token);
      setUploadSummary(`${uploaded.filename} is ready · ${uploaded.chunk_count} sections · ${uploaded.company}${uploaded.reporting_year ? ` · ${uploaded.reporting_year}` : ""}`);
      setUploadOpen(false);
      setToast("Report uploaded and indexed. You can ask questions about it now.");
      window.setTimeout(() => setToast(""), 4500);
    } catch (error) {
      const apiError = asApiError(error);
      if (apiError.status === 401) signOut("Your session expired. Please sign in again.");
      else setUploadError(apiError.message);
    } finally {
      setUploadBusy(false);
    }
  }

  async function runQuestion(question: string, questionMode = mode, appendUser = true) {
    if (!token || busy || !question.trim()) return;
    const cleanQuestion = question.trim();
    setBusy(true);
    setRequestError("");
    setFailedRequest(null);
    setMode(questionMode);
    setActiveHistoryId(null);
    if (appendUser) {
      setMessages((current) => [...current, { id: newId(), role: "user", content: cleanQuestion, createdAt: new Date().toISOString() }]);
    }

    try {
      if (questionMode === "chat") {
        const response = await api.chat(cleanQuestion, token);
        let sources: ChatSource[] = response.sources;
        if (response.sources.length > 0) {
          try {
            const retrieved = await api.search(cleanQuestion, token);
            const excerpts = new Map(retrieved.results.map((chunk) => [chunk.chunk_id, chunk.content]));
            sources = response.sources.map((source) => ({ ...source, excerpt: excerpts.get(source.chunk_id) }));
          } catch {
            // The chat endpoint already returned source names and page references; excerpts are best-effort.
          }
        }
        setMessages((current) => [...current, { id: newId(), role: "assistant", content: response.answer, createdAt: new Date().toISOString(), sources }]);
        await refreshHistory(token);
      } else {
        const response = await api.search(cleanQuestion, token);
        const content = response.result_count
          ? `Found ${response.result_count} matching passage${response.result_count === 1 ? "" : "s"}.`
          : "No matching passages were found. Try another question or upload a report first.";
        setMessages((current) => [...current, { id: newId(), role: "assistant", content, createdAt: new Date().toISOString(), searchResults: response.results, isSearch: true }]);
      }
    } catch (error) {
      const apiError = asApiError(error);
      if (apiError.status === 401) {
        signOut("Your session expired. Please sign in again.");
      } else {
        setRequestError(apiError.message);
        setFailedRequest({ question: cleanQuestion, mode: questionMode });
      }
    } finally {
      setBusy(false);
    }
  }

  function startNewQuestion() {
    setMessages([]);
    setActiveHistoryId(null);
    setRequestError("");
    setFailedRequest(null);
    setMode("chat");
  }

  function selectHistory(entry: HistoryEntry) {
    setActiveHistoryId(entry.id);
    setMode("chat");
    setRequestError("");
    setMessages([
      { id: `history-user-${entry.id}`, role: "user", content: entry.question, createdAt: entry.created_at },
      { id: `history-answer-${entry.id}`, role: "assistant", content: entry.answer, createdAt: entry.created_at, sources: entry.sources },
    ]);
  }

  const welcome = messages.length === 0;
  if (authLoading) {
    return <div className="grid min-h-screen place-items-center bg-[#f7f7f4] text-sm text-[#737a73]">Opening your workspace…</div>;
  }
  if (!token || !user) {
    return <AuthScreen busy={authBusy} error={authError} notice={authNotice} onSubmit={handleAuth} />;
  }

  return (
    <div className="flex h-screen min-h-[540px] overflow-hidden bg-[#f7f7f4] text-[#20251f]">
      <AppSidebar
        user={user}
        history={history}
        activeHistoryId={activeHistoryId}
        mobileOpen={mobileMenuOpen}
        onCloseMobile={() => setMobileMenuOpen(false)}
        onNewQuestion={startNewQuestion}
        onSelectHistory={selectHistory}
        onUpload={() => { setUploadError(""); setUploadOpen(true); }}
        onSignOut={() => signOut()}
      />

      <main className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-[65px] shrink-0 items-center justify-between border-b border-[#e8eae5] bg-[#fbfbf9] px-4 sm:px-7">
          <div className="flex min-w-0 items-center gap-2.5">
            <button className="grid size-8 shrink-0 place-items-center rounded-lg text-[#647067] hover:bg-[#eff1ed] md:hidden" onClick={() => setMobileMenuOpen(true)} aria-label="Open menu"><Menu size={18} /></button>
            <div className="min-w-0"><div className="truncate text-xs font-semibold text-[#3b453d]">{activeHistoryId ? "Previous question" : "Financial research"}</div><div className="mt-0.5 hidden text-[10px] text-[#929991] sm:block">Answers grounded in your uploaded reports</div></div>
          </div>
          <div className="flex items-center gap-2">
            {uploadSummary && <div className="hidden max-w-[280px] items-center gap-1.5 truncate rounded-full bg-[#eaf2eb] px-3 py-1.5 text-[10px] text-[#3d704e] lg:flex"><ShieldCheck size={12} className="shrink-0" /><span className="truncate">{uploadSummary}</span></div>}
            <button className="inline-flex h-9 items-center gap-2 rounded-lg border border-[#dfe4dd] bg-white px-3 text-[11px] font-semibold text-[#526055] transition hover:bg-[#f5f7f3]" onClick={() => { setUploadError(""); setUploadOpen(true); }}><UploadCloud size={14} className="text-[#4d7957]" /><span className="hidden sm:inline">Upload report</span><span className="sm:hidden">Upload</span></button>
          </div>
        </header>

        {welcome ? (
          <div className="chat-scrollbar min-h-0 flex-1 overflow-y-auto">
            <WelcomePanel hasUploadedDocument={Boolean(uploadSummary)} onSuggestion={(question) => runQuestion(question, "chat")} onUpload={() => { setUploadError(""); setUploadOpen(true); }} />
          </div>
        ) : (
          <div className="chat-scrollbar min-h-0 flex-1 overflow-y-auto px-4 py-6 sm:px-7" ref={scrollRef}>
            <div className="mx-auto max-w-[820px] space-y-6 pb-5">
              {messages.map((message) => <ChatMessage key={message.id} message={message} />)}
              {busy && <ChatMessage loading message={{ id: "pending", role: "assistant", content: "", createdAt: new Date().toISOString() }} />}
              {requestError && (
                <div className="ml-11 rounded-xl border border-[#f1d6d1] bg-[#fff9f8] p-3.5 text-xs text-[#8c4a40]" role="alert">
                  <div className="font-semibold">We couldn’t complete that request.</div><p className="mb-2 mt-1 leading-5">{requestError}</p>
                  {failedRequest && <button className="rounded-lg border border-[#e8c7c1] bg-white px-3 py-1.5 text-[11px] font-semibold text-[#8c4a40] hover:bg-[#fff2ef]" disabled={busy} onClick={() => runQuestion(failedRequest.question, failedRequest.mode, false)} type="button">Retry</button>}
                </div>
              )}
              <div />
            </div>
          </div>
        )}

        {!welcome && !busy && messages.length > 0 && (
          <div className="flex justify-center pb-1"><button className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[10px] text-[#929991] hover:bg-white hover:text-[#526055]" onClick={startNewQuestion} type="button"><Plus size={12} /> New question</button></div>
        )}
        <ChatComposer mode={mode} busy={busy} onModeChange={(nextMode) => setMode(nextMode)} onSend={(question) => runQuestion(question)} />
      </main>

      {uploadOpen && <UploadDialog busy={uploadBusy} error={uploadError} onClose={() => { if (!uploadBusy) setUploadOpen(false); }} onSubmit={handleUpload} />}
      {toast && <div className="fixed bottom-24 left-1/2 z-40 -translate-x-1/2 rounded-xl border border-[#d7e6d9] bg-white px-4 py-3 text-xs font-medium text-[#356347] shadow-lg" role="status">{toast}</div>}
    </div>
  );
}
