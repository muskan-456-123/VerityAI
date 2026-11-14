import axios from 'axios';

export type Verdict = 'CURRENT' | 'STALE' | 'CONTRADICTED' | 'UNSUPPORTED' | 'CONFLICTING' | 'STABLE';
export type Evidence = { source_id: string; title: string; url: string; domain: string; excerpt: string; relevance: number; published_date?: string | null; updated_date?: string | null; classification: 'supporting' | 'contradicting' | 'context' };
export type Claim = { claim_id: string; statement: string; category: string; temporal_sensitivity: string; search_query: string; verdict: Verdict; confidence: 'Low' | 'Moderate' | 'High'; confidence_rank: number; freshness: { label: string; explanation: string; temporal_change_evidence: boolean }; explanation: string; supporting_evidence: Evidence[]; contradicting_evidence: Evidence[]; evidence: Evidence[] };
export type Stage = { key: string; label: string; status: 'pending' | 'active' | 'complete' | 'error'; detail: string };
export type Report = { report_id: string; created_at: string; status: 'processing' | 'complete' | 'error'; source_text: string; stages: Stage[]; claims: Claim[]; corrected_answer: string | null; error: string | null };
export type HistoryItem = { report_id: string; created_at: string; status: Report['status']; preview: string; claim_count: number; stale_count: number; current_count: number; result_summary: string };

const client = axios.create({ baseURL: '/', timeout: 60_000, headers: { 'Content-Type': 'application/json' } });

export async function startVerification(text: string): Promise<string> {
  const { data } = await client.post<{ report_id: string }>('/api/verify', { text });
  return data.report_id;
}
export async function getReport(id: string): Promise<Report> {
  const { data } = await client.get<Report>(`/api/report/${encodeURIComponent(id)}`);
  return data;
}
export async function getHistory(): Promise<HistoryItem[]> {
  const { data } = await client.get<HistoryItem[]>('/api/history');
  return data;
}
export async function deleteReport(id: string): Promise<void> {
  await client.delete(`/api/report/${encodeURIComponent(id)}`);
}
export async function getHealth(): Promise<{ status: string; groq_configured: boolean; tavily_configured: boolean }> {
  const { data } = await client.get('/health');
  return data;
}
export function errorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) return error.response?.data?.detail || error.message || 'The request could not be completed.';
  return error instanceof Error ? error.message : 'Something went wrong.';
}
