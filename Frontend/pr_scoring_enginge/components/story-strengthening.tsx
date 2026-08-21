"use client";

import { useEffect, useState } from "react";
import { ApiError } from "@/lib/api/client";
import { analyzeStoryStrengthening, getStoryStrengthening, StrengtheningAnalysis, StrengtheningRecommendation, StrengtheningStatus, updateStrengtheningStatus } from "@/lib/opportunities";

const nextStatuses: { label: string; status: StrengtheningStatus }[] = [
  { label: "Start", status: "IN_PROGRESS" },
  { label: "Complete", status: "COMPLETED" },
  { label: "Dismiss", status: "DISMISSED" },
];

export function StoryStrengtheningPanel({ opportunityId }: { opportunityId: number }) {
  const [analysis, setAnalysis] = useState<StrengtheningAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [updating, setUpdating] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => { void getStoryStrengthening(opportunityId).then(setAnalysis).catch((reason) => setError(reason instanceof ApiError ? reason.message : "Unable to load story strengthening.")).finally(() => setLoading(false)); }, [opportunityId]);

  async function analyze() {
    try { setAnalyzing(true); setError(null); setAnalysis(await analyzeStoryStrengthening(opportunityId)); }
    catch (reason) { setError(reason instanceof ApiError ? reason.message : "Unable to analyze story strength."); }
    finally { setAnalyzing(false); }
  }

  async function updateStatus(recommendation: StrengtheningRecommendation, status: StrengtheningStatus) {
    try {
      setUpdating(recommendation.id); setError(null);
      const updated = await updateStrengtheningStatus(opportunityId, recommendation.id, status);
      setAnalysis((current) => current ? { ...current, recommendations: current.recommendations.map((item) => item.id === updated.id ? updated : item), progress: { completed: current.recommendations.filter((item) => item.id === updated.id ? updated.status === "COMPLETED" : item.status === "COMPLETED").length, total: current.progress.total } } : current);
    } catch (reason) { setError(reason instanceof ApiError ? reason.message : "Unable to update recommendation status."); }
    finally { setUpdating(null); }
  }

  if (loading) return <section className="angles-panel"><p className="muted-copy">Loading story strengthening…</p></section>;
  return <section className="angles-panel" aria-labelledby="story-strengthening-title">
    <div className="angles-heading"><div><p className="eyebrow">Story strengthening</p><h2 id="story-strengthening-title">Find out what could make this opportunity more compelling to the media.</h2></div><button className="primary-button" disabled={analyzing} onClick={() => void analyze()} type="button">{analyzing ? "Analyzing story…" : analysis ? "Re-analyze story" : "Analyze Story"}</button></div>
    {error && <p className="form-error" role="alert">{error}</p>}
    {!analysis && !error && <p className="muted-copy">Recommendations will be grounded in the current score explanation and confirmed opportunity information.</p>}
    {analysis && <><p className="muted-copy">{analysis.progress.completed} / {analysis.progress.total} recommendations completed</p>{!analysis.recommendations.length ? <p className="muted-copy">No supported weaknesses were identified from the current opportunity data.</p> : <div className="angles-list">{analysis.recommendations.map((recommendation) => <article className="angle-card" key={recommendation.id}><div className="angle-card-top"><div><p className={`potential potential-${recommendation.severity.toLowerCase()}`}>{recommendation.severity} priority</p><h3>{recommendation.title}</h3></div><strong>{recommendation.status.replace("_", " ")}</strong></div>{recommendation.angle_title && <p className="muted-copy">PR angle: {recommendation.angle_title}</p>}<h4>Affected dimension</h4><p>{recommendation.affected_dimension}</p><h4>Weakness</h4><p>{recommendation.weakness}</p><h4>Why it matters</h4><p>{recommendation.explanation}</p><h4>Recommended action</h4><p>{recommendation.recommendation}</p><h4>Evidence needed</h4><ul>{recommendation.required_evidence.map((item) => <li key={item}>{item}</li>)}</ul>{recommendation.required_information.length > 0 && <><h4>Information needed</h4><ul>{recommendation.required_information.map((item) => <li key={item}>{item}</li>)}</ul></>}<p className="muted-copy">{recommendation.expected_benefit}</p><div className="detail-actions">{recommendation.status !== "COMPLETED" && recommendation.status !== "DISMISSED" && nextStatuses.map((item) => <button className="secondary-button" disabled={updating === recommendation.id} key={item.status} onClick={() => void updateStatus(recommendation, item.status)} type="button">{updating === recommendation.id ? "Updating…" : item.label}</button>)}{recommendation.status !== "OPEN" && <button className="secondary-button" disabled={updating === recommendation.id} onClick={() => void updateStatus(recommendation, "OPEN")} type="button">Reopen</button>}</div></article>)}</div>}</>}
  </section>;
}
