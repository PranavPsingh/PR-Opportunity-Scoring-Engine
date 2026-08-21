"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ApiError } from "@/lib/api/client";
import { deleteOpportunity, getOpportunity, OpportunityRecord } from "@/lib/opportunities";
import { OpportunityScorePanel } from "@/components/opportunity-score";

export function OpportunityDetail({ opportunityId }: { opportunityId: number }) {
  const router = useRouter(); const [opportunity, setOpportunity] = useState<OpportunityRecord | null>(null); const [error, setError] = useState<string | null>(null); const [deleting, setDeleting] = useState(false);
  useEffect(() => { void getOpportunity(opportunityId).then(setOpportunity).catch((reason) => setError(reason instanceof ApiError ? reason.message : "Unable to load opportunity.")); }, [opportunityId]);
  async function remove() { if (!opportunity || !window.confirm(`Delete ${opportunity.title}? This cannot be undone.`)) return; try { setDeleting(true); await deleteOpportunity(opportunity.id); router.push("/opportunities"); } catch (reason) { setError(reason instanceof ApiError ? reason.message : "Unable to delete opportunity."); setDeleting(false); } }
  if (error) return <p className="form-error" role="alert">{error}</p>;
  if (!opportunity) return <p className="muted-copy">Loading opportunity…</p>;
  return <section className="client-detail"><Link className="back-link" href="/opportunities">← All opportunities</Link><div className="page-heading"><div><p className="eyebrow">{opportunity.status.replaceAll("_", " ")}</p><h1>{opportunity.title}</h1><p>{opportunity.client_name}</p></div><div className="detail-actions"><Link className="secondary-button" href={`/opportunities/${opportunity.id}/edit`}>Edit opportunity</Link><button className="danger-button" disabled={deleting} onClick={() => void remove()} type="button">{deleting ? "Deleting…" : "Delete"}</button></div></div><div className="detail-grid"><article><h2>Original client briefing</h2><p>{opportunity.client_briefing}</p></article><aside><h2>Story details</h2><dl><div><dt>Story type</dt><dd>{opportunity.story_type || "Not specified"}</dd></div><div><dt>Funding</dt><dd>{opportunity.funding_amount ? `${opportunity.funding_amount} ${opportunity.funding_stage}` : opportunity.funding_stage || "Not specified"}</dd></div><div><dt>Founder available</dt><dd>{opportunity.founder_available === null ? "Unknown" : opportunity.founder_available ? "Yes" : "No"}</dd></div><div><dt>Customers</dt><dd>{opportunity.customer_count ?? "Not specified"}</dd></div></dl></aside></div><OpportunityScorePanel opportunityId={opportunity.id} /></section>;
}
