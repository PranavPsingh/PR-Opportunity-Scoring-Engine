"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { ApiError } from "@/lib/api/client";
import { ClientInput, createClient, getClient, updateClient } from "@/lib/clients";

const emptyClient: ClientInput = { company_name: "", industry: "", location: "", website: "", description: "", company_size: "" };

export function ClientForm({ clientId }: { clientId?: number }) {
  const router = useRouter();
  const [values, setValues] = useState<ClientInput>(emptyClient);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(Boolean(clientId));
  const [saving, setSaving] = useState(false);
  const editing = Boolean(clientId);

  useEffect(() => {
    if (!clientId) return;
    void getClient(clientId).then((client) => setValues({ company_name: client.company_name, industry: client.industry, location: client.location, website: client.website, description: client.description, company_size: client.company_size })).catch((reason) => setError(reason instanceof ApiError ? reason.message : "Unable to load client.")).finally(() => setLoading(false));
  }, [clientId]);

  function updateField(field: keyof ClientInput, value: string) { setValues((current) => ({ ...current, [field]: value })); }
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setSaving(true); setError(null);
    try { const client = editing && clientId ? await updateClient(clientId, values) : await createClient(values); router.push(`/clients/${client.id}`); }
    catch (reason) { setError(reason instanceof ApiError ? reason.message : "Unable to save client."); }
    finally { setSaving(false); }
  }

  if (loading) return <p className="muted-copy">Loading client…</p>;
  return <section className="client-form-page"><p className="eyebrow">Client workspace</p><h1>{editing ? "Edit client" : "Add a client"}</h1><p className="lead">Capture the organisation’s core profile before evaluating PR opportunities.</p>{error ? <p className="form-error" role="alert">{error}</p> : null}<form className="client-form" onSubmit={(event) => void submit(event)}>
    <label>Company name<input onChange={(event) => updateField("company_name", event.target.value)} required value={values.company_name} /></label>
    <label>Industry<input onChange={(event) => updateField("industry", event.target.value)} required value={values.industry} /></label>
    <label>Location<input onChange={(event) => updateField("location", event.target.value)} required value={values.location} /></label>
    <label>Company size<input onChange={(event) => updateField("company_size", event.target.value)} placeholder="e.g. 51–200" required value={values.company_size} /></label>
    <label className="form-wide">Website<input onChange={(event) => updateField("website", event.target.value)} placeholder="https://example.com" required type="url" value={values.website} /></label>
    <label className="form-wide">Description<textarea onChange={(event) => updateField("description", event.target.value)} required rows={6} value={values.description} /></label>
    <div className="form-actions"><button className="secondary-button" onClick={() => router.back()} type="button">Cancel</button><button className="primary-button" disabled={saving} type="submit">{saving ? "Saving…" : editing ? "Save changes" : "Create client"}</button></div>
  </form></section>;
}
