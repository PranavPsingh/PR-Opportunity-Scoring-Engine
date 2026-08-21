import { ApiEnvelope, apiClient } from "@/lib/api/client";
import { csrfHeaders } from "@/lib/auth";

export type OpportunityStatus = "draft" | "ready_for_analysis" | "analyzed" | "archived";

export type OpportunityRecord = {
  id: number; client_id: number; client_name: string | null; title: string; description: string; story_type: string;
  funding_amount: string | null; funding_stage: string; founder_available: boolean | null; product_launched: boolean | null;
  product_launch_date: string | null; customer_count: number | null; revenue_information: string; geographic_relevance: string;
  target_audience: string; supporting_information: string; client_briefing: string; status: OpportunityStatus;
  created_at: string; updated_at: string;
};

export type OpportunityInput = Omit<OpportunityRecord, "id" | "client_name" | "created_at" | "updated_at">;
export type ExtractionStatus = "extracted" | "not_found" | "ambiguous";
export type ExtractedField = { value: string | number | boolean | string[] | null; confidence: number; source_text: string; extraction_status: ExtractionStatus };
export type ExtractionDecision = { action: "accepted" | "edited" | "rejected"; value: ExtractedField["value"] };
export type ExtractionRecord = { id: number; opportunity_id: number; provider: string; model_identifier: string; status: string; fields: Record<string, ExtractedField>; created_at: string; confirmation: { confirmed_by: { id: number; name: string; email: string; role: string } | null; decisions: Record<string, ExtractionDecision>; confirmed_at: string } | null };

export async function getOpportunities(clientId?: number): Promise<OpportunityRecord[]> {
  const suffix = clientId ? `?client_id=${clientId}` : "";
  const response = await apiClient.get<ApiEnvelope<{ opportunities: OpportunityRecord[] }>>(`opportunities/${suffix}`);
  return response.data.opportunities;
}
export async function getOpportunity(id: number): Promise<OpportunityRecord> { const response = await apiClient.get<ApiEnvelope<{ opportunity: OpportunityRecord }>>(`opportunities/${id}/`); return response.data.opportunity; }
export async function createOpportunity(input: OpportunityInput): Promise<OpportunityRecord> { const response = await apiClient.post<ApiEnvelope<{ opportunity: OpportunityRecord }>>("opportunities/", input, { headers: await csrfHeaders() }); return response.data.opportunity; }
export async function updateOpportunity(id: number, input: OpportunityInput): Promise<OpportunityRecord> { const response = await apiClient.put<ApiEnvelope<{ opportunity: OpportunityRecord }>>(`opportunities/${id}/`, input, { headers: await csrfHeaders() }); return response.data.opportunity; }
export async function deleteOpportunity(id: number): Promise<void> { await apiClient.delete(`opportunities/${id}/`, { headers: await csrfHeaders() }); }
export async function getLatestExtraction(id: number): Promise<ExtractionRecord | null> { const response = await apiClient.get<ApiEnvelope<{ extraction: ExtractionRecord | null }>>(`opportunities/${id}/extraction/`); return response.data.extraction; }
export async function extractInformation(id: number): Promise<ExtractionRecord> { const response = await apiClient.post<ApiEnvelope<{ extraction: ExtractionRecord }>>(`opportunities/${id}/extract/`, undefined, { headers: await csrfHeaders() }); return response.data.extraction; }
export async function confirmExtraction(id: number, extractionId: number, decisions: Record<string, ExtractionDecision>): Promise<{ extraction: ExtractionRecord; opportunity: OpportunityRecord }> { const response = await apiClient.post<ApiEnvelope<{ extraction: ExtractionRecord; opportunity: OpportunityRecord }>>(`opportunities/${id}/extraction/confirm/`, { extraction_id: extractionId, decisions }, { headers: await csrfHeaders() }); return response.data; }
