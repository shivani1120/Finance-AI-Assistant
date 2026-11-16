import { useEffect, useRef, useState, type FormEvent } from "react";
import { FileText, LoaderCircle, Upload, X } from "lucide-react";
import type { DocumentType, UploadInput } from "../api/types";

interface UploadDialogProps {
  busy: boolean;
  error: string;
  onClose: () => void;
  onSubmit: (input: UploadInput) => Promise<void>;
}

const documentTypes: { value: DocumentType; label: string }[] = [
  { value: "annual_report", label: "Annual report" },
  { value: "quarterly_report", label: "Quarterly report" },
  { value: "earnings_report", label: "Earnings report" },
  { value: "financial_statement", label: "Financial statement" },
  { value: "investor_presentation", label: "Investor presentation" },
  { value: "other", label: "Other" },
];

export function UploadDialog({ busy, error, onClose, onSubmit }: UploadDialogProps) {
  const [file, setFile] = useState<File | null>(null);
  const [company, setCompany] = useState("");
  const [reportingYear, setReportingYear] = useState("");
  const [documentType, setDocumentType] = useState<DocumentType>("annual_report");
  const fileInput = useRef<HTMLInputElement>(null);

  useEffect(() => {
    function onEscape(event: KeyboardEvent) {
      if (event.key === "Escape" && !busy) onClose();
    }
    window.addEventListener("keydown", onEscape);
    return () => window.removeEventListener("keydown", onEscape);
  }, [busy, onClose]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!file || !company.trim() || busy) return;
    await onSubmit({
      file,
      company: company.trim(),
      reportingYear: reportingYear ? Number(reportingYear) : undefined,
      documentType,
    });
  }

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-[#18221b]/35 p-0 backdrop-blur-[2px] sm:items-center sm:p-5" onMouseDown={(event) => { if (event.target === event.currentTarget && !busy) onClose(); }}>
      <section aria-labelledby="upload-title" aria-modal="true" className="w-full max-w-[480px] rounded-t-3xl border border-[#e5e8e2] bg-[#fff] p-5 shadow-[0_24px_80px_rgba(18,38,24,.2)] sm:rounded-2xl sm:p-6" role="dialog">
        <div className="flex items-start justify-between gap-4">
          <div><span className="mb-3 grid size-10 place-items-center rounded-xl bg-[#eaf2eb] text-[#326b4b]"><FileText size={18} /></span><h2 className="text-lg font-semibold tracking-tight text-[#263029]" id="upload-title">Add a financial report</h2><p className="mt-1 text-xs leading-5 text-[#828a82]">The PDF will be processed into searchable sections.</p></div>
          <button aria-label="Close upload dialog" className="grid size-8 place-items-center rounded-lg text-[#838b84] hover:bg-[#f2f4f0]" disabled={busy} onClick={onClose} type="button"><X size={17} /></button>
        </div>

        <form className="mt-5 space-y-3.5" onSubmit={handleSubmit}>
          <div>
            <span className="mb-1.5 block text-[11px] font-semibold text-[#505b52]">PDF file</span>
            <button className="flex min-h-[60px] w-full items-center gap-3 rounded-xl border border-dashed border-[#cdd8ce] bg-[#fafbf9] px-3.5 py-3 text-left transition hover:border-[#83a78a] hover:bg-[#f5f9f4]" onClick={() => fileInput.current?.click()} type="button">
              <span className="grid size-9 shrink-0 place-items-center rounded-lg bg-white text-[#53775a] shadow-sm"><Upload size={16} /></span>
              <span className="min-w-0 flex-1"><span className="block truncate text-xs font-medium text-[#39453c]">{file?.name ?? "Choose a PDF from your device"}</span><span className="mt-1 block text-[10px] text-[#969e96]">PDF files only</span></span>
            </button>
            <input accept="application/pdf,.pdf" className="sr-only" onChange={(event) => setFile(event.target.files?.[0] ?? null)} ref={fileInput} type="file" />
          </div>
          <label className="block"><span className="mb-1.5 block text-[11px] font-semibold text-[#505b52]">Company</span><input className="h-10 w-full rounded-lg border border-[#dfe4dd] bg-white px-3 text-xs outline-none focus:border-[#6e9b79] focus:ring-4 focus:ring-[#4a8d6d]/10" value={company} onChange={(event) => setCompany(event.target.value)} maxLength={200} placeholder="e.g. Acme Corporation" required /></label>
          <div className="grid grid-cols-2 gap-3">
            <label className="block"><span className="mb-1.5 block text-[11px] font-semibold text-[#505b52]">Reporting year <span className="font-normal text-[#9aa19b]">optional</span></span><input className="h-10 w-full rounded-lg border border-[#dfe4dd] bg-white px-3 text-xs outline-none focus:border-[#6e9b79] focus:ring-4 focus:ring-[#4a8d6d]/10" value={reportingYear} onChange={(event) => setReportingYear(event.target.value)} type="number" min={1900} max={2100} placeholder="2025" /></label>
            <label className="block"><span className="mb-1.5 block text-[11px] font-semibold text-[#505b52]">Report type</span><select className="h-10 w-full rounded-lg border border-[#dfe4dd] bg-white px-3 text-xs outline-none focus:border-[#6e9b79] focus:ring-4 focus:ring-[#4a8d6d]/10" value={documentType} onChange={(event) => setDocumentType(event.target.value as DocumentType)}>{documentTypes.map((type) => <option key={type.value} value={type.value}>{type.label}</option>)}</select></label>
          </div>
          {error && <div className="rounded-lg bg-[#fbefed] px-3 py-2.5 text-xs leading-5 text-[#a44238]" role="alert">{error}</div>}
          <div className="flex justify-end gap-2 border-t border-[#eff0ed] pt-4">
            <button className="h-9 rounded-lg px-3 text-xs font-medium text-[#727a73] transition hover:bg-[#f4f5f2]" disabled={busy} onClick={onClose} type="button">Cancel</button>
            <button className="inline-flex h-9 items-center gap-2 rounded-lg bg-[#1f6349] px-3.5 text-xs font-semibold text-white transition hover:bg-[#174c38] disabled:opacity-60" disabled={busy || !file || !company.trim()} type="submit">{busy ? <LoaderCircle className="animate-spin" size={14} /> : <Upload size={14} />}{busy ? "Processing report…" : "Upload report"}</button>
          </div>
          {busy && <p className="text-center text-[10px] text-[#8a928a]">The server is extracting and indexing text. This can take a moment.</p>}
        </form>
      </section>
    </div>
  );
}
