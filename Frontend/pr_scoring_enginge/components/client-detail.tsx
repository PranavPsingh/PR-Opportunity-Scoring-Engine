"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { ApiError } from "@/lib/api/client";
import { ClientRecord, deleteClient, getClient } from "@/lib/clients";

export function ClientDetail({ clientId }: { clientId: number }) {
  const router = useRouter();
  const [client, setClient] = useState<ClientRecord | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);
  useEffect(() => { void getClient(clientId).then(setClient).catch((reason) => setError(reason instanceof ApiError ? reason.message : "Unable to load client.")); }, [clientId]);
  async function remove() {
    if (!client || !window.confirm(`Delete ${client.company_name}? This cannot be undone.`)) return;
    try { setDeleting(true); await deleteClient(client.id); router.push("/clients"); }
    catch (reason) { setError(reason instanceof ApiError ? reason.message : "Unable to delete client."); setDeleting(false); }
  }
  if (error) return <p className="form-error" role="alert">{error}</p>;
  if (!client) return <p className="muted-copy">Loading client…</p>;
  return <section className="client-detail"><Link className="back-link" href="/clients">← All clients</Link><div className="page-heading"><div><p className="eyebrow">{client.industry}</p><h1>{client.company_name}</h1><p>{client.location} · {client.company_size}</p></div><div className="detail-actions"><Link className="secondary-button" href={`/clients/${client.id}/edit`}>Edit client</Link><button className="danger-button" disabled={deleting} onClick={() => void remove()} type="button">{deleting ? "Deleting…" : "Delete"}</button></div></div><div className="detail-grid"><article><h2>Company profile</h2><p>{client.description}</p></article><aside><h2>Organisation details</h2><dl><div><dt>Website</dt><dd><a href={client.website} rel="noreferrer" target="_blank">{client.website}</a></dd></div><div><dt>Created by</dt><dd>{client.created_by?.name ?? "Deleted user"}</dd></div><div><dt>Added</dt><dd>{new Intl.DateTimeFormat(undefined, { dateStyle: "medium" }).format(new Date(client.created_at))}</dd></div></dl></aside></div></section>;
}
