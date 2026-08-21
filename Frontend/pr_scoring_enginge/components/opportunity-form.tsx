"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ApiError } from "@/lib/api/client";
import { getClients, ClientRecord } from "@/lib/clients";
import { createOpportunity, getOpportunity, OpportunityInput, OpportunityRecord, updateOpportunity } from "@/lib/opportunities";

const emptyOpportunity: OpportunityInput = { client_id: 0, title: "", description: "", story_type: "", funding_amount: null, funding_stage: "", founder_available: null, product_launched: null, product_launch_date: null, customer_count: null, revenue_information: "", geographic_relevance: "", target_audience: "", supporting_information: "", client_briefing: "", status: "draft" };
const statuses = ["draft", "ready_for_analysis", "analyzed", "archived"] as const;

function nullableBoolean(value: string): boolean | null { return value === "" ? null : value === "true"; }
function toInput(opportunity: OpportunityRecord): OpportunityInput { return { client_id: opportunity.client_id, title: opportunity.title, description: opportunity.description, story_type: opportunity.story_type, funding_amount: opportunity.funding_amount, funding_stage: opportunity.funding_stage, founder_available: opportunity.founder_available, product_launched: opportunity.product_launched, product_launch_date: opportunity.product_launch_date, customer_count: opportunity.customer_count, revenue_information: opportunity.revenue_information, geographic_relevance: opportunity.geographic_relevance, target_audience: opportunity.target_audience, supporting_information: opportunity.supporting_information, client_briefing: opportunity.client_briefing, status: opportunity.status }; }

export function OpportunityForm({ opportunityId }: { opportunityId?: number }) {
  const router = useRouter(); const editing = Boolean(opportunityId);
  const [clients, setClients] = useState<ClientRecord[]>([]); const [values, setValues] = useState<OpportunityInput>(emptyOpportunity);
  const [error, setError] = useState<string | null>(null); const [loading, setLoading] = useState(true); const [saving, setSaving] = useState(false);
  useEffect(() => { void Promise.all([getClients(), opportunityId ? getOpportunity(opportunityId) : Promise.resolve(null)]).then(([availableClients, opportunity]) => { setClients(availableClients); if (opportunity) setValues(toInput(opportunity)); }).catch((reason) => setError(reason instanceof ApiError ? reason.message : "Unable to load opportunity intake." )).finally(() => setLoading(false)); }, [opportunityId]);
  function setField<K extends keyof OpportunityInput>(field: K, value: OpportunityInput[K]) { setValues((current) => ({ ...current, [field]: value })); }
  async function submit(event: FormEvent<HTMLFormElement>) { event.preventDefault(); setError(null); setSaving(true); try { const opportunity = editing && opportunityId ? await updateOpportunity(opportunityId, values) : await createOpportunity(values); router.push(`/opportunities/${opportunity.id}`); } catch (reason) { setError(reason instanceof ApiError ? reason.message : "Unable to save opportunity."); } finally { setSaving(false); } }
  if (loading) return <p className="muted-copy">Loading opportunity intake…</p>;
  return <section className="opportunity-form-page"><p className="eyebrow">Opportunity intake</p><h1>{editing ? "Edit opportunity" : "New opportunity"}</h1><p className="lead">Record the story and its original client briefing for future consultant review and analysis.</p>{error ? <p className="form-error" role="alert">{error}</p> : null}<form className="client-form" onSubmit={(event) => void submit(event)}>
    <label>Client<select aria-label="Client" required value={values.client_id || ""} onChange={(event) => setField("client_id", Number(event.target.value))}><option value="">Select a client</option>{clients.map((client) => <option key={client.id} value={client.id}>{client.company_name}</option>)}</select></label>
    <label>Status<select value={values.status} onChange={(event) => setField("status", event.target.value as OpportunityInput["status"])}>{statuses.map((status) => <option key={status} value={status}>{status.replaceAll("_", " ")}</option>)}</select></label>
    <label className="form-wide">Opportunity/story title<input required value={values.title} onChange={(event) => setField("title", event.target.value)} /></label>
    <label className="form-wide">Story description<textarea rows={4} value={values.description} onChange={(event) => setField("description", event.target.value)} /></label>
    <label>Story type<input placeholder="e.g. Funding, launch, event" value={values.story_type} onChange={(event) => setField("story_type", event.target.value)} /></label>
    <label>Funding stage<input placeholder="e.g. Series A" value={values.funding_stage} onChange={(event) => setField("funding_stage", event.target.value)} /></label>
    <label>Funding amount<input min="0" step="0.01" type="number" value={values.funding_amount ?? ""} onChange={(event) => setField("funding_amount", event.target.value || null)} /></label>
    <label>Customer count<input min="0" type="number" value={values.customer_count ?? ""} onChange={(event) => setField("customer_count", event.target.value ? Number(event.target.value) : null)} /></label>
    <label>Product launched?<select value={values.product_launched === null ? "" : String(values.product_launched)} onChange={(event) => setField("product_launched", nullableBoolean(event.target.value))}><option value="">Unknown</option><option value="true">Yes</option><option value="false">No</option></select></label>
    <label>Product launch date<input type="date" value={values.product_launch_date ?? ""} onChange={(event) => setField("product_launch_date", event.target.value || null)} /></label>
    <label>Founder available for media?<select value={values.founder_available === null ? "" : String(values.founder_available)} onChange={(event) => setField("founder_available", nullableBoolean(event.target.value))}><option value="">Unknown</option><option value="true">Yes</option><option value="false">No</option></select></label>
    <label>Target audience<input value={values.target_audience} onChange={(event) => setField("target_audience", event.target.value)} /></label>
    <label className="form-wide">Revenue information<textarea rows={3} value={values.revenue_information} onChange={(event) => setField("revenue_information", event.target.value)} /></label>
    <label className="form-wide">Geographic relevance<textarea rows={3} value={values.geographic_relevance} onChange={(event) => setField("geographic_relevance", event.target.value)} /></label>
    <label className="form-wide">Supporting information<textarea rows={3} value={values.supporting_information} onChange={(event) => setField("supporting_information", event.target.value)} /></label>
    <label className="form-wide"><strong>Original client briefing</strong><textarea aria-label="Original client briefing" required rows={10} placeholder="Paste the client email, message, or briefing exactly as received." value={values.client_briefing} onChange={(event) => setField("client_briefing", event.target.value)} /></label>
    <div className="form-actions"><button className="secondary-button" onClick={() => router.back()} type="button">Cancel</button><button className="primary-button" disabled={saving} type="submit">{saving ? "Saving…" : editing ? "Save changes" : "Create opportunity"}</button></div>
  </form></section>;
}
