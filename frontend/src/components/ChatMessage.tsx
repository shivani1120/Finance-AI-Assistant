import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Check, ChevronDown, Copy, FileText, Sparkles } from "lucide-react";
import type { ChatMessageData } from "../api/types";

interface ChatMessageProps {
  message: ChatMessageData;
  loading?: boolean;
}

function timeLabel(value: string) {
  return new Date(value).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
}

export function ChatMessage({ message, loading = false }: ChatMessageProps) {
  const [copied, setCopied] = useState(false);
  const isUser = message.role === "user";

  async function copyAnswer() {
    try {
      await navigator.clipboard.writeText(message.content);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1600);
    } catch {
      setCopied(false);
    }
  }

  return (
    <article className={`flex gap-3 ${isUser ? "flex-row-reverse" : "flex-row"}`}>
      <div className={`mt-0.5 grid size-8 shrink-0 place-items-center rounded-full ${isUser ? "bg-[#e7ebe6] text-[#58645a]" : "bg-[#e5efe8] text-[#276044]"}`}>
        {isUser ? <span className="text-[10px] font-bold">YOU</span> : <Sparkles size={15} />}
      </div>
      <div className={`min-w-0 max-w-[min(760px,88%)] ${isUser ? "text-right" : "text-left"}`}>
        <div className={`mb-1.5 flex items-center gap-2 text-[10px] text-[#929992] ${isUser ? "justify-end" : "justify-start"}`}>
          <span className="font-semibold text-[#69736a]">{isUser ? "You" : "Finance Assistant"}</span>
          <span>{timeLabel(message.createdAt)}</span>
        </div>
        {loading ? (
          <div className="inline-flex items-center gap-2 rounded-2xl rounded-tl-md border border-[#e5e9e3] bg-white px-4 py-3 text-xs text-[#768078] shadow-[0_2px_10px_rgba(31,49,37,.035)]">
            <span className="flex gap-1" aria-label="Assistant is thinking"><i className="size-1.5 animate-bounce rounded-full bg-[#72977d] [animation-delay:-.2s]" /><i className="size-1.5 animate-bounce rounded-full bg-[#72977d] [animation-delay:-.1s]" /><i className="size-1.5 animate-bounce rounded-full bg-[#72977d]" /></span>
            Searching your reports and preparing an answer…
          </div>
        ) : (
          <div className={`rounded-2xl px-4 py-3.5 text-sm leading-[1.7] ${isUser ? "inline-block rounded-tr-md bg-[#e8efe9] text-[#26352b]" : "border border-[#e8eae5] bg-white text-[#303831] shadow-[0_2px_10px_rgba(31,49,37,.035)]"}`}>
            {message.isSearch && <div className="mb-2 flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-[.08em] text-[#598065]"><FileText size={12} /> Passage search</div>}
            {isUser ? (
              <p className="m-0 whitespace-pre-wrap">{message.content}</p>
            ) : (
              <div className="markdown-content text-left">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
              </div>
            )}
            {!isUser && message.searchResults && message.searchResults.length > 0 && (
              <section className="mt-3 border-t border-[#edf0eb] pt-3 text-left">
                <div className="mb-2 text-[10px] font-semibold uppercase tracking-[.1em] text-[#6b776e]">Matching passages ({message.searchResults.length})</div>
                <div className="space-y-2">
                  {message.searchResults.map((result) => (
                    <div className="rounded-lg bg-[#f6f8f5] p-3" key={result.chunk_id}>
                      <div className="mb-1.5 text-[10px] font-semibold text-[#50745a]">{result.filename}{result.page_number ? ` · Page ${result.page_number}` : ""} · {result.company}</div>
                      <p className="m-0 line-clamp-5 text-xs leading-5 text-[#5d675f]">{result.content}</p>
                    </div>
                  ))}
                </div>
              </section>
            )}
            {!isUser && message.sources && message.sources.length > 0 && (
              <details className="group mt-3 border-t border-[#edf0eb] pt-2.5 text-left">
                <summary className="flex cursor-pointer list-none items-center gap-1.5 text-[11px] font-semibold text-[#547660] hover:text-[#244f38]">
                  <ChevronDown className="transition-transform group-open:rotate-180" size={14} />
                  Sources ({message.sources.length})
                </summary>
                <div className="mt-2 space-y-2">
                  {message.sources.map((source) => (
                    <div className="rounded-lg bg-[#f6f8f5] p-3" key={`${source.document_id}:${source.chunk_id}`}>
                      <div className="text-[11px] font-semibold text-[#455c4a]">{source.filename}{source.page_number ? ` · Page ${source.page_number}` : ""}</div>
                      {source.excerpt && <p className="mb-0 mt-1.5 text-xs leading-5 text-[#6a736b]">{source.excerpt}</p>}
                    </div>
                  ))}
                </div>
              </details>
            )}
          </div>
        )}
        {!isUser && !loading && (
          <button className="mt-1.5 inline-flex items-center gap-1 rounded-md px-2 py-1 text-[10px] text-[#89918a] transition hover:bg-white hover:text-[#4c5a4e]" onClick={copyAnswer} type="button" aria-label="Copy assistant response">
            {copied ? <Check size={12} /> : <Copy size={12} />}{copied ? "Copied" : "Copy"}
          </button>
        )}
      </div>
    </article>
  );
}
