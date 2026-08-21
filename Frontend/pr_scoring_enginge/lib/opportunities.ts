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
export type ScoreFactor = { factor: string; impact: number; source_field: string; source_value: string | number | boolean | null; reason: string };
export type ScoreDimension = { dimension: string; score: number; positive_factors: ScoreFactor[]; negative_factors: ScoreFactor[]; missing_information: string[]; scoring_signals_used: ScoreFactor[] };
export type ScoreCalculation = { formula: string; weighted_total: string; rounded_overall_score: number; dimensions: { dimension: string; score: number; weight: string; weighted_score: string }[] };
export type OpportunityScore = { id: number; opportunity_id: number; overall_score: number; potential: "HIGH" | "MEDIUM" | "LOW"; newsworthiness_score: number; media_appeal_score: number; timeliness_score: number; credibility_score: number; audience_interest_score: number; scoring_version: string; scored_at: string; metadata: { dimensions: Record<string, ScoreDimension>; weights: Record<string, string>; calculation: ScoreCalculation; overall_explanation: { strong_points: ScoreFactor[]; areas_holding_back: ScoreFactor[] } } };
export type PRAngle = { id: number; opportunity_id: number; generation_id: number; title: string; summary: string; potential_score: number; potential_level: "HIGH" | "MEDIUM" | "LOW"; rationale: string; target_audience: string[]; media_categories: string[]; key_message: string; supporting_facts: { fact: string; source_field: string }[]; required_evidence: string[]; risks: string[]; missing_information: string[]; selected: boolean; generated_at: string };
export type StrengtheningStatus = "OPEN" | "IN_PROGRESS" | "COMPLETED" | "DISMISSED";
export type StrengtheningRecommendation = { id: number; analysis_id: number; opportunity_id: number; angle_id: number | null; angle_title: string | null; title: string; weakness: string; affected_dimension: string; severity: "HIGH" | "MEDIUM" | "LOW"; explanation: string; recommendation: string; required_information: string[]; required_evidence: string[]; expected_benefit: string; status: StrengtheningStatus; source_factors: string[]; created_at: string; updated_at: string };
export type StrengtheningAnalysis = { id: number; opportunity_id: number; score_id: number | null; created_at: string; recommendations: StrengtheningRecommendation[]; progress: { completed: number; total: number } };

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
export async function getLatestScore(id: number): Promise<OpportunityScore | null> { const response = await apiClient.get<ApiEnvelope<{ score: OpportunityScore | null }>>(`opportunities/${id}/score/`); return response.data.score; }
export async function scoreOpportunity(id: number): Promise<OpportunityScore> { const response = await apiClient.post<ApiEnvelope<{ score: OpportunityScore }>>(`opportunities/${id}/score/`, undefined, { headers: await csrfHeaders() }); return response.data.score; }
export async function getScoreHistory(id: number): Promise<OpportunityScore[]> { const response = await apiClient.get<ApiEnvelope<{ scores: OpportunityScore[] }>>(`opportunities/${id}/scores/`); return response.data.scores; }
export async function getPRAngles(id: number): Promise<PRAngle[]> { const response = await apiClient.get<ApiEnvelope<{ angles: PRAngle[] }>>(`opportunities/${id}/angles/`); return response.data.angles; }
export async function generatePRAngles(id: number): Promise<PRAngle[]> { const response = await apiClient.post<ApiEnvelope<{ angles: PRAngle[] }>>(`opportunities/${id}/angles/generate/`, undefined, { headers: await csrfHeaders() }); return response.data.angles; }
export async function selectPRAngle(opportunityId: number, angleId: number, selected: boolean): Promise<PRAngle> { const response = await apiClient.patch<ApiEnvelope<{ angle: PRAngle }>>(`opportunities/${opportunityId}/angles/${angleId}/`, { selected }, { headers: await csrfHeaders() }); return response.data.angle; }
export async function getStoryStrengthening(id: number): Promise<StrengtheningAnalysis | null> { const response = await apiClient.get<ApiEnvelope<{ analysis: StrengtheningAnalysis | null }>>(`opportunities/${id}/strengthening/`); return response.data.analysis; }
export async function analyzeStoryStrengthening(id: number): Promise<StrengtheningAnalysis> { const response = await apiClient.post<ApiEnvelope<{ analysis: StrengtheningAnalysis }>>(`opportunities/${id}/strengthening/analyze/`, undefined, { headers: await csrfHeaders() }); return response.data.analysis; }
export async function updateStrengtheningStatus(opportunityId: number, recommendationId: number, status: StrengtheningStatus): Promise<StrengtheningRecommendation> { const response = await apiClient.patch<ApiEnvelope<{ recommendation: StrengtheningRecommendation }>>(`opportunities/${opportunityId}/strengthening/${recommendationId}/`, { status }, { headers: await csrfHeaders() }); return response.data.recommendation; }
