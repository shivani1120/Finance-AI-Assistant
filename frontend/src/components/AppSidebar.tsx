import { FileText, HelpCircle, Landmark, MessageSquareText, Plus, Upload, X } from "lucide-react";
import type { HistoryEntry, User } from "../api/types";

interface AppSidebarProps {
  user: User;
  history: HistoryEntry[];
  activeHistoryId: number | null;
  mobileOpen: boolean;
  onCloseMobile: () => void;
  onNewQuestion: () => void;
  onSelectHistory: (entry: HistoryEntry) => void;
  onUpload: () => void;
  onSignOut: () => void;
}

function initials(email: string) {
  return email.split("@")[0].slice(0, 2).toUpperCase();
}

export function AppSidebar({
  user,
  history,
  activeHistoryId,
  mobileOpen,
  onCloseMobile,
  onNewQuestion,
  onSelectHistory,
  onUpload,
  onSignOut,
}: AppSidebarProps) {
  return (
    <>
      {mobileOpen && <button className="fixed inset-0 z-30 bg-black/30 md:hidden" onClick={onCloseMobile} aria-label="Close menu" />}
      <aside className={`fixed inset-y-0 left-0 z-40 flex w-[278px] shrink-0 flex-col border-r border-[#e8eae5] bg-white transition-transform duration-200 md:static md:z-auto md:translate-x-0 ${mobileOpen ? "translate-x-0" : "-translate-x-full"}`}>
        <div className="flex h-[72px] items-center justify-between px-5">
          <div className="flex items-center gap-3">
            <span className="grid size-9 place-items-center rounded-xl bg-[#e7f0e9] text-[#225d45]"><Landmark size={18} /></span>
            <div><div className="text-sm font-semibold tracking-tight text-[#20251f]">Finance AI</div><div className="text-[10px] text-[#8a918a]">ASSISTANT</div></div>
          </div>
          <button className="grid size-8 place-items-center rounded-lg text-[#8a918a] hover:bg-[#f3f4f0] md:hidden" onClick={onCloseMobile} aria-label="Close sidebar"><X size={17} /></button>
        </div>

        <div className="px-4 pb-4">
          <button className="flex h-10 w-full items-center justify-center gap-2 rounded-xl bg-[#1f6349] px-3 text-xs font-semibold text-white shadow-sm transition hover:bg-[#174c38]" onClick={() => { onNewQuestion(); onCloseMobile(); }}>
            <Plus size={16} /> New question
          </button>
          <button className="mt-2 flex h-10 w-full items-center gap-2 rounded-xl border border-[#e6e9e3] px-3 text-xs font-medium text-[#4e5b50] transition hover:bg-[#f7f8f5]" onClick={() => { onUpload(); onCloseMobile(); }}>
            <Upload size={15} className="text-[#467a5c]" /> Upload a report
          </button>
        </div>

        <div className="mx-4 border-t border-[#eff0ed]" />
        <div className="flex min-h-0 flex-1 flex-col px-3 pt-4">
          <div className="flex items-center justify-between px-2 pb-2">
            <span className="text-[10px] font-semibold uppercase tracking-[.12em] text-[#8c938c]">Recent questions</span>
            <span className="text-[10px] text-[#a0a69f]">{history.length}</span>
          </div>
          {history.length === 0 ? (
            <div className="px-2 pt-2 text-xs leading-5 text-[#9aa19a]">Your questions will appear here after you chat.</div>
          ) : (
            <div className="chat-scrollbar flex-1 space-y-1 overflow-y-auto">
              {history.map((entry) => (
                <button key={entry.id} className={`group flex w-full items-start gap-2.5 rounded-lg px-2.5 py-2.5 text-left transition ${activeHistoryId === entry.id ? "bg-[#eef4ee] text-[#245b42]" : "text-[#687169] hover:bg-[#f6f7f4] hover:text-[#28312a]"}`} onClick={() => { onSelectHistory(entry); onCloseMobile(); }}>
                  <MessageSquareText className="mt-0.5 shrink-0 opacity-65" size={14} />
                  <span className="line-clamp-2 text-xs leading-[1.45]">{entry.question}</span>
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="mx-4 border-t border-[#eff0ed]" />
        <div className="space-y-1 px-3 py-3">
          <a className="flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-xs font-medium text-[#6b746c] transition hover:bg-[#f6f7f4] hover:text-[#2c4737]" href="/docs" target="_blank" rel="noreferrer">
            <HelpCircle size={15} /> API guide
          </a>
          <a className="flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-xs font-medium text-[#6b746c] transition hover:bg-[#f6f7f4] hover:text-[#2c4737]" href="/docs#/documents/upload_document_documents_upload_post" target="_blank" rel="noreferrer">
            <FileText size={15} /> Upload API details
          </a>
        </div>

        <div className="border-t border-[#eff0ed] p-3">
          <div className="flex items-center gap-2.5 rounded-xl px-2 py-2">
            <span className="grid size-8 shrink-0 place-items-center rounded-full bg-[#e8eee8] text-[10px] font-bold text-[#315943]">{initials(user.email)}</span>
            <span className="min-w-0 flex-1"><span className="block truncate text-xs font-semibold text-[#39433b]">{user.email}</span><span className="mt-0.5 block text-[10px] capitalize text-[#919890]">{user.role} account</span></span>
            <button className="rounded-md px-2 py-1 text-[10px] font-medium text-[#858d85] hover:bg-[#f4f5f1] hover:text-[#4a554c]" onClick={onSignOut}>Sign out</button>
          </div>
        </div>
      </aside>
    </>
  );
}
