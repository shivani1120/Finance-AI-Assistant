import { useRef, useState, type FormEvent, type KeyboardEvent } from "react";
import { ArrowUp, Search, Sparkles } from "lucide-react";

export type QuestionMode = "chat" | "search";

interface ChatComposerProps {
  mode: QuestionMode;
  busy: boolean;
  onModeChange: (mode: QuestionMode) => void;
  onSend: (question: string) => void;
}

export function ChatComposer({ mode, busy, onModeChange, onSend }: ChatComposerProps) {
  const formRef = useRef<HTMLFormElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const [question, setQuestion] = useState("");

  function submit() {
    const value = question.trim();
    if (!value || busy) return;
    onSend(value);
    setQuestion("");
    if (inputRef.current) {
      inputRef.current.value = "";
      inputRef.current.style.height = "auto";
    }
  }

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    submit();
  }

  function onKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      formRef.current?.requestSubmit();
    }
  }

  return (
    <div className="border-t border-[#e9ebe6] bg-[#fbfbf9] px-4 pb-4 pt-3 sm:px-7 sm:pb-5">
      <div className="mx-auto max-w-[820px]">
        <div className="mb-2 flex items-center gap-1.5">
          <button className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-[10px] font-semibold transition ${mode === "chat" ? "bg-[#e6efe8] text-[#2b6245]" : "text-[#858d86] hover:bg-[#f0f2ed]"}`} onClick={() => onModeChange("chat")} type="button" aria-pressed={mode === "chat"}><Sparkles size={12} /> Ask AI</button>
          <button className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-[10px] font-semibold transition ${mode === "search" ? "bg-[#e6efe8] text-[#2b6245]" : "text-[#858d86] hover:bg-[#f0f2ed]"}`} onClick={() => onModeChange("search")} type="button" aria-pressed={mode === "search"}><Search size={12} /> Find passages</button>
          <span className="ml-auto hidden text-[10px] text-[#a0a69f] sm:block">Enter to send · Shift + Enter for a new line</span>
        </div>
        <form className="relative rounded-2xl border border-[#dfe4dd] bg-white shadow-[0_4px_18px_rgba(41,55,44,.045)] transition focus-within:border-[#8eb49a] focus-within:shadow-[0_0_0_3px_rgba(54,123,79,.08)]" ref={formRef} onSubmit={onSubmit}>
          <textarea
            aria-label="Ask about your reports"
            className="block max-h-40 min-h-[58px] w-full resize-none bg-transparent py-[18px] pl-4 pr-16 text-sm leading-6 text-[#263029] outline-none placeholder:text-[#9aa19b] sm:pl-5"
            maxLength={2000}
            onChange={(event) => setQuestion(event.currentTarget.value)}
            onKeyDown={onKeyDown}
            onInput={(event) => {
              event.currentTarget.style.height = "auto";
              event.currentTarget.style.height = `${Math.min(event.currentTarget.scrollHeight, 160)}px`;
            }}
            placeholder={mode === "chat" ? "Ask a question about your financial reports…" : "Search for a topic, metric, or phrase…"}
            ref={inputRef}
            rows={1}
            value={question}
          />
          <button aria-label={mode === "chat" ? "Send question" : "Search passages"} className="absolute bottom-2.5 right-2.5 grid size-9 place-items-center rounded-xl bg-[#1f6349] text-white transition hover:bg-[#174c38] disabled:cursor-not-allowed disabled:bg-[#c8d2ca]" disabled={busy || !question.trim()} type="submit"><ArrowUp size={18} /></button>
        </form>
        <p className="mt-2 text-center text-[10px] leading-4 text-[#969d96]">Review the cited passages before relying on an AI-generated answer.</p>
      </div>
    </div>
  );
}
