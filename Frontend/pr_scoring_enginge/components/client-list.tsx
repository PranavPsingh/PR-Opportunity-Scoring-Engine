"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

import { ApiError } from "@/lib/api/client";
import { filterClients } from "@/lib/client-filtering";
import { ClientRecord, getClients } from "@/lib/clients";

export function ClientList() {
  const [clients, setClients] = useState<ClientRecord[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({ search: "", industry: "", companySize: "" });
  const loadClients = useCallback(async () => {
    try { setError(null); setClients(await getClients()); }
    catch (reason) { setError(reason instanceof ApiError ? reason.message : "Unable to load clients."); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => void loadClients(), 0);
    return () => window.clearTimeout(timer);
  }, [loadClients]);
  const visibleClients = useMemo(() => filterClients(clients, filters), [clients, filters]);
  const industries = useMemo(() => [...new Set(clients.map((client) => client.industry))].sort(), [clients]);
  const companySizes = useMemo(() => [...new Set(clients.map((client) => client.company_size))].sort(), [clients]);

  return <section className="client-workspace">
    <div className="page-heading"><div><p className="eyebrow">Client workspace</p><h1>Client portfolio</h1><p>Organisations currently being assessed for PR opportunities.</p></div><Link className="primary-button" href="/clients/new">Add client</Link></div>
    <div className="client-filters" aria-label="Client filters">
      <label>Search<input aria-label="Search clients" onChange={(event) => setFilters((current) => ({ ...current, search: event.target.value }))} placeholder="Company, industry, or location" value={filters.search} /></label>
      <label>Industry<select aria-label="Filter by industry" onChange={(event) => setFilters((current) => ({ ...current, industry: event.target.value }))} value={filters.industry}><option value="">All industries</option>{industries.map((industry) => <option key={industry}>{industry}</option>)}</select></label>
      <label>Company size<select aria-label="Filter by company size" onChange={(event) => setFilters((current) => ({ ...current, companySize: event.target.value }))} value={filters.companySize}><option value="">All sizes</option>{companySizes.map((companySize) => <option key={companySize}>{companySize}</option>)}</select></label>
    </div>
    {error ? <p className="form-error" role="alert">{error}</p> : null}
    {loading ? <p className="muted-copy">Loading clients…</p> : null}
    {!loading && !error && visibleClients.length === 0 ? <div className="empty-state"><h2>No clients found</h2><p>Adjust your filters or add the first organisation to your portfolio.</p></div> : null}
    <div className="client-grid">{visibleClients.map((client) => <Link className="client-card" href={`/clients/${client.id}`} key={client.id}><span className="client-card-industry">{client.industry}</span><h2>{client.company_name}</h2><p>{client.location} · {client.company_size}</p><span>View client →</span></Link>)}</div>
  </section>;
}
