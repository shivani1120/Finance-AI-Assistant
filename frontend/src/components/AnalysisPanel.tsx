import { useEffect, useState } from "react";
import { BarChart3, Check, LoaderCircle, X } from "lucide-react";
import { api } from "../api/client";
import { ApiError } from "../api/types";
import type { AnalysisDocument, CompareReportsResponse, MetricEvidence } from "../api/types";

interface AnalysisPanelProps {
  token: string;
  onClose: () => void;
}

const metricLabels = [
  ["revenue", "Revenue"],
  ["operating_profit", "Operating profit"],
  ["net_income", "Net income"],
  ["operating_cash_flow", "Operating cash flow"],
  ["total_debt", "Total debt"],
] as const;

function showAmount(metric: MetricEvidence | null) {
  if (!metric) return "Not found clearly";
  return `${metric.value.toLocaleString(undefined, { maximumFractionDigits: 2 })} ${metric.unit}`;
}

export function AnalysisPanel({ token, onClose }: AnalysisPanelProps) {
  const [documents, setDocuments] = useState<AnalysisDocument[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [result, setResult] = useState<CompareReportsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [comparing, setComparing] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    api.analysisDocuments(token)
      .then((items) => { if (!cancelled) setDocuments(items); })
      .catch((cause: unknown) => {
        if (!cancelled) setError(cause instanceof ApiError ? cause.message : "Could not load your reports.");
      })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [token]);

  function toggle(documentId: string) {
    setSelected((current) => current.includes(documentId)
      ? current.filter((id) => id !== documentId)
      : current.length < 5 ? [...current, documentId] : current);
    setResult(null);
  }

  async function compare() {
    setComparing(true);
    setError("");
    setResult(null);
    try {
      setResult(await api.compareReports(selected, token));
    } catch (cause) {
      setError(cause instanceof ApiError ? cause.message : "Could not compare the selected reports.");
    } finally {
      setComparing(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#172019]/35 p-3 sm:p-6" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}>
      <section aria-labelledby="analysis-title" aria-modal="true" className="flex max-h-[92vh] w-full max-w-4xl flex-col overflow-hidden rounded-2xl border border-[#e4e8e1] bg-[#fbfcfa] shadow-2xl" role="dialog">
        <header className="flex items-start justify-between border-b border-[#e9ece6] px-5 py-4 sm:px-7">
          <div className="flex gap-3">
            <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-[#eaf2eb] text-[#2d674a]"><BarChart3 size={19} /></span>
            <div><h2 className="text-base font-semibold text-[#263129]" id="analysis-title">Compare financial reports</h2><p className="mt-1 text-xs text-[#778078]">Extract figures, calculate margins and growth, and inspect the source page.</p></div>
          </div>
          <button aria-label="Close comparison" className="grid size-8 place-items-center rounded-lg text-[#788078] hover:bg-[#eff2ed]" onClick={onClose} type="button"><X size={17} /></button>
        </header>

        <div className="chat-scrollbar min-h-0 flex-1 overflow-y-auto p-5 sm:p-7">
          {!result && <>
            <p className="mb-3 text-xs font-semibold text-[#445047]">Choose 2–5 reports to compare</p>
            {loading ? <div className="flex items-center gap-2 py-8 text-xs text-[#778078]"><LoaderCircle className="animate-spin" size={16} /> Loading your reports…</div> : documents.length === 0 ? <p className="rounded-xl border border-dashed border-[#d8dfd7] p-5 text-xs leading-5 text-[#788178]">No uploaded reports found. Upload at least two reports first.</p> : (
              <div className="space-y-2">
                {documents.map((document) => {
                  const checked = selected.includes(document.document_id);
                  return <button aria-pressed={checked} className={`flex w-full items-center gap-3 rounded-xl border p-3.5 text-left transition ${checked ? "border-[#80a98a] bg-[#f0f6ef]" : "border-[#e5e9e3] bg-white hover:border-[#c5d0c4]"}`} key={document.document_id} onClick={() => toggle(document.document_id)} type="button">
                    <span className={`grid size-5 shrink-0 place-items-center rounded-md border ${checked ? "border-[#39704d] bg-[#39704d] text-white" : "border-[#cdd4cc] bg-white text-transparent"}`}><Check size={13} /></span>
                    <span className="min-w-0 flex-1"><span className="block truncate text-xs font-semibold text-[#344039]">{document.company} {document.reporting_year ?? ""}</span><span className="mt-1 block truncate text-[11px] text-[#828a82]">{document.filename} · {document.chunk_count} passages</span></span>
                  </button>;
                })}
              </div>
            )}
            <p className="mt-3 text-[10px] leading-4 text-[#929991]">Figures are only included when the extracted amount, quote, and report page can be verified. Some report formats may not yield a clear figure.</p>
            {error && <p className="mt-3 rounded-lg bg-[#fff0ed] px-3 py-2 text-xs text-[#8c4a40]" role="alert">{error}</p>}
            <div className="mt-5 flex justify-end"><button className="inline-flex h-10 items-center gap-2 rounded-lg bg-[#1f6349] px-4 text-xs font-semibold text-white transition hover:bg-[#174c38] disabled:cursor-not-allowed disabled:opacity-50" disabled={selected.length < 2 || comparing || loading} onClick={compare} type="button">{comparing && <LoaderCircle className="animate-spin" size={14} />}{comparing ? "Analyzing reports…" : `Compare ${selected.length || ""} reports`}</button></div>
          </>}

          {result && <>
            <div className="mb-4 flex items-center justify-between"><div><h3 className="text-sm font-semibold text-[#344039]">Comparison results</h3><p className="mt-1 text-[11px] text-[#828a82]">Calculated values are shown only when source units match.</p></div><button className="text-xs font-semibold text-[#39704d] hover:underline" onClick={() => setResult(null)} type="button">Choose reports</button></div>
            <div className="space-y-4">
              {result.reports.map((report) => <article className="overflow-hidden rounded-xl border border-[#e4e8e1] bg-white" key={report.document_id}>
                <div className="border-b border-[#edf0eb] bg-[#f7f9f6] px-4 py-3"><h4 className="text-xs font-semibold text-[#344039]">{report.company} {report.reporting_year ?? ""}</h4><p className="mt-1 truncate text-[10px] text-[#858d85]">{report.filename}</p></div>
                <div className="grid gap-x-6 sm:grid-cols-2">
                  {metricLabels.map(([key, label]) => {
                    const evidence = report.metrics[key];
                    return <div className="border-b border-[#f0f2ee] px-4 py-3" key={key}>
                      <div className="flex items-center justify-between gap-2"><span className="text-[11px] text-[#68736a]">{label}</span><span className={`text-right text-xs font-semibold ${evidence ? "text-[#344039]" : "text-[#9aa19a]"}`}>{showAmount(evidence)}</span></div>
                      {evidence && <p className="mt-1.5 text-[10px] leading-4 text-[#8a928a]">Page {evidence.page_number}: “{evidence.quote}”</p>}
                    </div>;
                  })}
                  <div className="px-4 py-3"><span className="text-[11px] text-[#68736a]">Operating margin</span><span className="float-right text-xs font-semibold text-[#344039]">{report.operating_margin_percent == null ? "Unavailable" : `${report.operating_margin_percent}%`}</span><p className="mt-1.5 text-[10px] text-[#8a928a]">Operating profit ÷ revenue</p></div>
                  <div className="px-4 py-3"><span className="text-[11px] text-[#68736a]">Revenue growth</span><span className="float-right text-xs font-semibold text-[#344039]">{report.revenue_growth_percent == null ? "Unavailable" : `${report.revenue_growth_percent}%`}</span><p className="mt-1.5 text-[10px] text-[#8a928a]">Year-over-year, same company and units</p></div>
                </div>
              </article>)}
            </div>
            <p className="mt-4 rounded-lg bg-[#f0f4ef] p-3 text-[10px] leading-4 text-[#68746a]">{result.note}</p>
          </>}
        </div>
      </section>
    </div>
  );
}
