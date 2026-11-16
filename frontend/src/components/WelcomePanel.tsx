import { ArrowUpRight, ChartNoAxesCombined, FileSearch, FileUp, Landmark } from "lucide-react";

const suggestions = [
  { icon: ChartNoAxesCombined, title: "Revenue trends", prompt: "How did revenue change compared with the previous year?" },
  { icon: FileSearch, title: "Find key risks", prompt: "What key business risks are described in this report?" },
  { icon: Landmark, title: "Compare cash flow", prompt: "Summarize the main operating cash flow trends." },
];

interface WelcomePanelProps {
  hasUploadedDocument: boolean;
  onSuggestion: (prompt: string) => void;
  onUpload: () => void;
}

export function WelcomePanel({ hasUploadedDocument, onSuggestion, onUpload }: WelcomePanelProps) {
  return (
    <div className="mx-auto flex w-full max-w-[740px] flex-col items-center px-5 pb-10 pt-10 text-center sm:pt-16">
      <div className="mb-5 grid size-14 place-items-center rounded-2xl border border-[#dce8de] bg-[#eaf2eb] text-[#2d674a] shadow-[0_3px_12px_rgba(42,88,56,.06)]"><ChartNoAxesCombined size={23} /></div>
      <p className="text-[10px] font-semibold uppercase tracking-[.16em] text-[#4b805b]">Financial report research</p>
      <h1 className="mt-2 max-w-lg text-3xl font-semibold leading-tight tracking-[-.05em] text-[#222923] sm:text-[38px]">Hi! What would you like to understand?</h1>
      <p className="mt-3 max-w-md text-sm leading-6 text-[#777f78]">Ask questions across your uploaded financial reports. Answers include the sources used.</p>

      {!hasUploadedDocument && (
        <button className="mt-7 flex w-full max-w-[510px] items-center gap-3 rounded-2xl border border-dashed border-[#b8cabb] bg-[#f4f8f3] p-4 text-left transition hover:border-[#7eaa88] hover:bg-[#eef5ee]" onClick={onUpload} type="button">
          <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-white text-[#39704d] shadow-sm"><FileUp size={18} /></span>
          <span className="min-w-0 flex-1"><span className="block text-xs font-semibold text-[#34493a]">{hasUploadedDocument ? "Add another report" : "Upload a report"}</span><span className="mt-1 block text-[11px] text-[#7d887f]">Add a PDF to search its contents and cite relevant pages.</span></span>
          <ArrowUpRight size={15} className="text-[#718978]" />
        </button>
      )}

      <div className="mt-9 grid w-full grid-cols-1 gap-2.5 text-left sm:grid-cols-3">
        {suggestions.map(({ icon: Icon, title, prompt }) => (
          <button className="group rounded-xl border border-[#e7e9e4] bg-white p-3.5 text-left transition hover:-translate-y-0.5 hover:border-[#c4d6c7] hover:shadow-[0_6px_20px_rgba(31,49,37,.055)]" key={title} onClick={() => onSuggestion(prompt)} type="button">
            <span className="mb-3 grid size-8 place-items-center rounded-lg bg-[#f1f5f0] text-[#4d7658]"><Icon size={15} /></span>
            <span className="block text-xs font-semibold text-[#3a453c]">{title}</span>
            <span className="mt-1.5 block text-[11px] leading-[1.45] text-[#808881]">{prompt}</span>
          </button>
        ))}
      </div>
      <p className="mt-7 text-[10px] leading-5 text-[#a0a59f]">Suggested questions are examples. The assistant answers from documents in your account.</p>
    </div>
  );
}
