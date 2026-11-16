import { useState, type FormEvent } from "react";
import { ArrowRight, Landmark, LockKeyhole, Mail } from "lucide-react";

type AuthMode = "login" | "register";

interface AuthScreenProps {
  busy: boolean;
  error: string;
  notice: string;
  onSubmit: (mode: AuthMode, email: string, password: string) => Promise<"registered" | "signed-in" | void>;
}

export function AuthScreen({ busy, error, notice, onSubmit }: AuthScreenProps) {
  const [mode, setMode] = useState<AuthMode>("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const registering = mode === "register";

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const result = await onSubmit(mode, email.trim(), password);
    if (result === "registered") setMode("login");
  }

  return (
    <main className="grid min-h-screen bg-[#f7f7f4] lg:grid-cols-[1.1fr_.9fr]">
      <section className="relative hidden overflow-hidden bg-[#17392f] p-12 text-white lg:flex lg:flex-col lg:justify-between xl:p-16">
        <div className="absolute -right-40 -top-32 h-[30rem] w-[30rem] rounded-full border border-white/10" />
        <div className="absolute -right-16 -top-8 h-[22rem] w-[22rem] rounded-full border border-white/10" />
        <div className="relative flex items-center gap-3 font-semibold tracking-tight">
          <span className="grid size-10 place-items-center rounded-xl bg-white/10"><Landmark size={20} /></span>
          Finance AI Assistant
        </div>
        <div className="relative max-w-xl pb-10">
          <div className="mb-5 text-xs font-semibold uppercase tracking-[.18em] text-[#a9cbb8]">Know your numbers</div>
          <h1 className="text-5xl font-semibold leading-[1.08] tracking-[-.055em] xl:text-6xl">Make every report easier to understand.</h1>
          <p className="mt-6 max-w-md text-base leading-7 text-white/65">Bring your financial reports together. Search the details and get answers linked back to their sources.</p>
        </div>
        <div className="relative text-xs text-white/45">AI answers should be checked against the original report.</div>
      </section>

      <section className="flex min-h-screen items-center justify-center px-5 py-10 sm:px-8">
        <div className="w-full max-w-[400px]">
          <div className="mb-9 flex items-center gap-3 font-semibold tracking-tight text-[#17392f] lg:hidden">
            <span className="grid size-10 place-items-center rounded-xl bg-[#e4eee6]"><Landmark size={20} /></span>
            Finance AI Assistant
          </div>
          <div className="mb-8">
            <p className="text-xs font-semibold uppercase tracking-[.15em] text-[#3d7a60]">Your private workspace</p>
            <h2 className="mt-2 text-3xl font-semibold tracking-[-.045em] text-[#20251f]">{registering ? "Create your account" : "Welcome back"}</h2>
            <p className="mt-2 text-sm leading-6 text-[#737a73]">{registering ? "Create an account to upload and explore your reports." : "Sign in to continue researching your reports."}</p>
          </div>

          <div className="mb-6 grid grid-cols-2 rounded-xl bg-[#eceee9] p-1" role="tablist" aria-label="Account access">
            <button className={`rounded-lg px-3 py-2.5 text-sm font-medium transition ${!registering ? "bg-white text-[#20251f] shadow-sm" : "text-[#727972] hover:text-[#20251f]"}`} onClick={() => setMode("login")} type="button" role="tab" aria-selected={!registering}>Sign in</button>
            <button className={`rounded-lg px-3 py-2.5 text-sm font-medium transition ${registering ? "bg-white text-[#20251f] shadow-sm" : "text-[#727972] hover:text-[#20251f]"}`} onClick={() => setMode("register")} type="button" role="tab" aria-selected={registering}>Create account</button>
          </div>

          <form className="space-y-4" onSubmit={handleSubmit}>
            <label className="block">
              <span className="mb-1.5 block text-xs font-semibold text-[#465047]">Email address</span>
              <span className="relative block">
                <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[#9aa29b]" size={17} aria-hidden="true" />
                <input autoComplete="username" className="h-12 w-full rounded-xl border border-[#dfe3dc] bg-white pl-10 pr-3 text-sm outline-none transition placeholder:text-[#a5aba5] focus:border-[#5a9879] focus:ring-4 focus:ring-[#4a8d6d]/10" type="email" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="you@example.com" required maxLength={320} />
              </span>
            </label>
            <label className="block">
              <span className="mb-1.5 block text-xs font-semibold text-[#465047]">Password</span>
              <span className="relative block">
                <LockKeyhole className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[#9aa29b]" size={17} aria-hidden="true" />
                <input autoComplete={registering ? "new-password" : "current-password"} className="h-12 w-full rounded-xl border border-[#dfe3dc] bg-white pl-10 pr-3 text-sm outline-none transition placeholder:text-[#a5aba5] focus:border-[#5a9879] focus:ring-4 focus:ring-[#4a8d6d]/10" type="password" value={password} onChange={(event) => setPassword(event.target.value)} placeholder={registering ? "At least 12 characters" : "Your password"} required minLength={registering ? 12 : 1} maxLength={128} />
              </span>
            </label>
            {notice && <p className="rounded-lg bg-[#e9f3eb] px-3 py-2.5 text-sm text-[#2e6b4c]" role="status">{notice}</p>}
            {error && <p className="rounded-lg bg-[#fbefed] px-3 py-2.5 text-sm text-[#a44238]" role="alert">{error}</p>}
            <button className="group flex h-12 w-full items-center justify-center gap-2 rounded-xl bg-[#1e6249] px-4 text-sm font-semibold text-white shadow-sm transition hover:bg-[#174d39] disabled:cursor-wait disabled:opacity-60" disabled={busy} type="submit">
              {busy ? "Please wait…" : registering ? "Create account" : "Sign in"}
              {!busy && <ArrowRight className="transition-transform group-hover:translate-x-0.5" size={16} />}
            </button>
          </form>
          <p className="mt-6 text-center text-xs leading-5 text-[#858c85]">Your password is sent over HTTPS and stored as a hash by the API. Never share your account password.</p>
        </div>
      </section>
    </main>
  );
}
