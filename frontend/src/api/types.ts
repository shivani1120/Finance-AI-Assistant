export type UserRole = "user" | "admin";

export interface User {
  id: number;
  email: string;
  role: UserRole;
}

export interface AuthToken {
  access_token: string;
  token_type: "bearer";
  expires_in: number;
}

export type DocumentType =
  | "annual_report"
  | "quarterly_report"
  | "earnings_report"
  | "financial_statement"
  | "investor_presentation"
  | "other";

export interface UploadedDocument {
  document_id: string;
  filename: string;
  company: string;
  reporting_year: number | null;
  document_type: DocumentType;
  chunk_count: number;
  status: string;
}

export interface ChatSource {
  source_id: string;
  document_id: string;
  filename: string;
  page_number: number | null;
  chunk_id: string;
  excerpt?: string;
}

export interface RetrievedChunk {
  chunk_id: string;
  document_id: string;
  filename: string;
  company: string;
  reporting_year: number | null;
  document_type: DocumentType;
  page_number: number | null;
  content: string;
  distance: number;
  similarity_score: number;
}

export interface RetrievalResponse {
  question: string;
  result_count: number;
  results: RetrievedChunk[];
}

export interface ChatResponse {
  answer: string;
  sources: ChatSource[];
}

export interface HistoryEntry {
  id: number;
  question: string;
  answer: string;
  sources: ChatSource[];
  created_at: string;
}

export interface HistoryPage {
  items: HistoryEntry[];
  limit: number;
  offset: number;
  total: number;
}

export interface ChatMessageData {
  id: string;
  role: "user" | "assistant";
  content: string;
  createdAt: string;
  sources?: ChatSource[];
  searchResults?: RetrievedChunk[];
  isSearch?: boolean;
}

interface UploadMetadata {
  company: string;
  reportingYear?: number;
  documentType: DocumentType;
}

export type UploadInput =
  | (UploadMetadata & { source: "file"; file: File })
  | (UploadMetadata & { source: "url"; url: string });

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status?: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}
