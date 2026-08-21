"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { ApiError } from "@/lib/api/client";
import { DashboardOpportunity, DashboardSummary, getDashboardSummary } from "@/lib/opportunities";

const emptySummary: DashboardSummary = { total_opportunities: 0, potential_counts: { HIGH: 0, MEDIUM: 0, LOW: 0 }, average_score: null, requiring_attention: 0, score_buckets: { "80-100": 0, "60-79": 0, "40-59": 0, "0-39": 0 }, recent_opportunities: [], top_opportunities: [], attention_opportunities: [], trends: [] };

function formatDate(value: string | null) { return value ? new Intl.DateTimeFormat("en", { dateStyle: "medium" }).format(new Date(value)) : "Not analyzed"; }
function potentialClass(value: DashboardOpportunity["potential"]) { return value ? `potential potential-${value.toLowerCase()}` : "potential potential-none"; }

export function Dashboard() {
  const [summary, setSummary] = useState<DashboardSummary>(emptySummary);
  const [filters, setFilters] = useState({ search: "", potential: "", status: "", min_score: "", max_score: "", analyzed_from: "", analyzed_to: "" });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadSummary() {
    setLoading(true); setError(null);
    try { setSummary(await getDashboardSummary(filters)); } catch (reason) { setError(reason instanceof ApiError ? reason.message : "Unable to load dashboard data."); } finally { setLoading(false); }
  }
  useEffect(() => {
    getDashboardSummary().then(setSummary).catch((reason) => setError(reason instanceof ApiError ? reason.message : "Unable to load dashboard data.")).finally(() => setLoading(false));
  }, []);

  function updateFilter(field: keyof typeof filters, value: string) { setFilters((current) => ({ ...current, [field]: value })); }
  const kpis = [
    ["Total opportunities", summary.total_opportunities, "/opportunities"],
    ["High potential", summary.potential_counts.HIGH, "/opportunities?potential=HIGH"],
    ["Medium potential", summary.potential_counts.MEDIUM, "/opportunities?potential=MEDIUM"],
    ["Low potential", summary.potential_counts.LOW, "/opportunities?potential=LOW"],
    ["Average score", summary.average_score === null ? "—" : `${summary.average_score}/100`, "/opportunities"],
    ["Requires attention", summary.requiring_attention, "/opportunities?status=draft"],
  ] as const;

  return <div className="dashboard-page">
    <div className="page-heading"><div><p className="eyebrow">Consultant overview</p><h1>Opportunity pipeline</h1><p>See where the strongest stories are, and what needs your attention next.</p></div><Link className="primary-button" href="/opportunities/new">New opportunity</Link></div>
    <form className="dashboard-filters" onSubmit={(event) => { event.preventDefault(); void loadSummary(); }}>
      <label>Search<input value={filters.search} onChange={(event) => updateFilter("search", event.target.value)} placeholder="Opportunity or client" /></label>
      <label>Potential<select value={filters.potential} onChange={(event) => updateFilter("potential", event.target.value)}><option value="">All potentials</option><option value="HIGH">High</option><option value="MEDIUM">Medium</option><option value="LOW">Low</option></select></label>
      <label>Status<select value={filters.status} onChange={(event) => updateFilter("status", event.target.value)}><option value="">All statuses</option><option value="draft">Draft</option><option value="ready_for_analysis">Ready for analysis</option><option value="analyzed">Analyzed</option><option value="archived">Archived</option></select></label>
      <label>Score from<input inputMode="numeric" type="number" min="0" max="100" value={filters.min_score} onChange={(event) => updateFilter("min_score", event.target.value)} /></label>
      <label>Score to<input inputMode="numeric" type="number" min="0" max="100" value={filters.max_score} onChange={(event) => updateFilter("max_score", event.target.value)} /></label>
      <label>Analyzed from<input type="date" value={filters.analyzed_from} onChange={(event) => updateFilter("analyzed_from", event.target.value)} /></label>
      <label>Analyzed to<input type="date" value={filters.analyzed_to} onChange={(event) => updateFilter("analyzed_to", event.target.value)} /></label>
      <button className="primary-button" disabled={loading} type="submit">Apply filters</button>
    </form>
    {error ? <div className="dashboard-error" role="alert"><p>{error}</p><button className="secondary-button" onClick={() => void loadSummary()} type="button">Retry</button></div> : null}
    {loading ? <p className="dashboard-loading" role="status">Loading your opportunity pipeline…</p> : null}
    {!loading && !error && summary.total_opportunities === 0 ? <div className="empty-state"><h2>No opportunities found</h2><p>Create an opportunity or adjust the current filters to see your pipeline.</p><Link className="primary-button" href="/opportunities/new">Create opportunity</Link></div> : null}
    {!loading && !error && summary.total_opportunities > 0 ? <>
      <section className="kpi-grid" aria-label="Pipeline summary">{kpis.map(([label, value, href]) => <Link className="kpi-card" href={href} key={label}><span>{label}</span><strong>{value}</strong></Link>)}</section>
      <div className="dashboard-columns"><section className="dashboard-panel"><div className="panel-heading"><div><p className="eyebrow">Potential mix</p><h2>Opportunity distribution</h2></div></div><div className="distribution-list">{(["HIGH", "MEDIUM", "LOW"] as const).map((level) => <div className="distribution-row" key={level}><span className={potentialClass(level)}>{level}</span><div className="distribution-track"><span className={`distribution-fill fill-${level.toLowerCase()}`} style={{ width: `${summary.potential_counts[level] / Math.max(summary.total_opportunities, 1) * 100}%` }} /></div><strong>{summary.potential_counts[level]}</strong></div>)}</div></section>
        <section className="dashboard-panel"><div className="panel-heading"><div><p className="eyebrow">Score overview</p><h2>Pipeline strength</h2></div></div><div className="score-buckets">{Object.entries(summary.score_buckets).map(([range, count]) => <div key={range}><strong>{count}</strong><span>{range}</span></div>)}</div></section></div>
      <section className="dashboard-panel"><div className="panel-heading"><div><p className="eyebrow">Highest scoring</p><h2>Top opportunities</h2></div></div>{summary.top_opportunities.length ? <div className="top-opportunity-list">{summary.top_opportunities.map((item) => <Link href={`/opportunities/${item.id}`} key={item.id}><span><strong>{item.title}</strong><small>{item.client_name}</small></span><b>{item.score}<small className={potentialClass(item.potential)}>{item.potential}</small></b></Link>)}</div> : <p className="muted-copy">No analyzed opportunities yet.</p>}</section>
      <section className="dashboard-panel"><div className="panel-heading"><div><p className="eyebrow">Latest analysis</p><h2>Recently analyzed</h2></div></div>{summary.recent_opportunities.length ? <div className="dashboard-table-wrap"><table className="dashboard-table"><thead><tr><th>Client</th><th>Opportunity</th><th>Score</th><th>Potential</th><th>Status</th><th>Last analyzed</th><th>Actions</th></tr></thead><tbody>{summary.recent_opportunities.map((item) => <tr key={item.id}><td>{item.client_name}</td><td><Link href={`/opportunities/${item.id}`}>{item.title}</Link></td><td><strong>{item.score}</strong></td><td><span className={potentialClass(item.potential)}>{item.potential}</span></td><td>{item.status.replaceAll("_", " ")}</td><td>{formatDate(item.last_analyzed)}</td><td><Link href={`/opportunities/${item.id}`}>View opportunity</Link><Link href={`/opportunities/${item.id}`}>View analysis</Link></td></tr>)}</tbody></table></div> : <p className="muted-copy">No analyzed opportunities yet.</p>}</section>
      <div className="dashboard-columns"><section className="dashboard-panel"><div className="panel-heading"><div><p className="eyebrow">Needs action</p><h2>Opportunities requiring attention</h2></div></div>{summary.attention_opportunities.length ? <div className="attention-list">{summary.attention_opportunities.map((item) => <Link href={`/opportunities/${item.id}`} key={item.id}><span><strong>{item.title}</strong><small>{item.client_name}</small></span><small>{item.attention_reasons.join(" · ")}</small></Link>)}</div> : <p className="muted-copy">Nothing requires attention right now.</p>}</section>
        <section className="dashboard-panel"><div className="panel-heading"><div><p className="eyebrow">Persisted history</p><h2>Opportunity trends</h2></div></div>{summary.trends.length ? <div className="trend-list">{summary.trends.slice(-7).map((trend) => <div key={trend.date}><span>{formatDate(trend.date)}</span><strong>{trend.average_score}</strong><small>{trend.analyzed_count} analyzed · {trend.high_count} high</small></div>)}</div> : <p className="muted-copy">No historical score data yet.</p>}</section></div>
    </> : null}
  </div>;
}