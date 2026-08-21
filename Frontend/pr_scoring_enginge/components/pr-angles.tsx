"use client";

import { useEffect, useState } from "react";
import { ApiError } from "@/lib/api/client";
import { generatePRAngles, getPRAngles, PRAngle, selectPRAngle } from "@/lib/opportunities";

export function PRAnglesPanel({ opportunityId }: { opportunityId: number }) {
  const [angles, setAngles] = useState<PRAngle[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<number | null>(null);

  useEffect(() => { void getPRAngles(opportunityId).then(setAngles).catch((reason) => setError(reason instanceof ApiError ? reason.message : "Unable to load PR angles.")).finally(() => setLoading(false)); }, [opportunityId]);
  async function generate() { try { setGenerating(true); setError(null); setAngles(await generatePRAngles(opportunityId)); setExpanded(null); } catch (reason) { setError(reason instanceof ApiError ? reason.message : "Unable to generate PR angles."); } finally { setGenerating(false); } }
  async function select(angle: PRAngle) { try { const updated = await selectPRAngle(opportunityId, angle.id, !angle.selected); setAngles((items) => items.map((item) => item.id === updated.id ? updated : item)); } catch (reason) { setError(reason instanceof ApiError ? reason.message : "Unable to update the selected angle."); } }

  if (loading) return <section className="angles-panel"><p className="muted-copy">Loading PR angles…</p></section>;
  return <section className="angles-panel"><div className="angles-heading"><div><p className="eyebrow">PR angles</p><h2>Potential ways to position this opportunity</h2></div><button className="primary-button" disabled={generating} onClick={() => void generate()} type="button">{generating ? "Extracting facts and generating PR angles…" : angles.length ? "Regenerate PR angles" : "Generate PR Angles"}</button></div>{error && <p className="form-error" role="alert">{error}</p>}{!angles.length && !error ? <p className="muted-copy">Generate grounded, distinct story angles. Gemini extracts facts in the background; extracted text is not displayed.</p> : <div className="angles-list">{angles.map((angle) => <article className="angle-card" key={angle.id}><div className="angle-card-top"><div><h3>{angle.title}</h3><p className={`potential potential-${angle.potential_level.toLowerCase()}`}>{angle.potential_level} potential</p></div><strong className="angle-score">{angle.potential_score}<span> / 100</span></strong></div><p>{angle.summary}</p><h4>Why this angle works</h4><p>{angle.rationale}</p><h4>Supporting facts</h4><ul>{angle.supporting_facts.map((fact) => <li key={`${fact.source_field}-${fact.fact}`}>{fact.fact}</li>)}</ul><button className="secondary-button" onClick={() => void select(angle)} type="button">{angle.selected ? "Selected" : "Mark as selected"}</button><button className="secondary-button" onClick={() => setExpanded(expanded === angle.id ? null : angle.id)} type="button">{expanded === angle.id ? "Hide details" : "View details"}</button>{expanded === angle.id && <div className="angle-details"><h4>Key message</h4><p>{angle.key_message}</p><h4>Target audience</h4><p>{angle.target_audience.join(", ") || "Not specified"}</p><h4>Media categories</h4><p>{angle.media_categories.join(", ") || "Not specified"}</p><h4>What could make this angle stronger</h4><ul>{angle.required_evidence.map((item) => <li key={item}>{item}</li>)}</ul>{angle.missing_information.length > 0 && <><h4>Missing information</h4><ul>{angle.missing_information.map((item) => <li key={item}>{item}</li>)}</ul></>}<h4>Risks and weaknesses</h4><ul>{angle.risks.map((item) => <li key={item}>{item}</li>)}</ul></div>}</article>)}</div>}</section>;
}
