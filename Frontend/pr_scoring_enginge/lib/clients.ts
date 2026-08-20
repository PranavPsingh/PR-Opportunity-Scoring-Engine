import { ApiEnvelope, apiClient } from "@/lib/api/client";
import { AuthenticatedUser, csrfHeaders } from "@/lib/auth";

export type ClientRecord = {
  id: number;
  company_name: string;
  industry: string;
  location: string;
  website: string;
  description: string;
  company_size: string;
  created_by: AuthenticatedUser | null;
  authorized_consultant_ids: number[];
  created_at: string;
  updated_at: string;
};

export type ClientInput = Pick<ClientRecord, "company_name" | "industry" | "location" | "website" | "description" | "company_size">;

export async function getClients(): Promise<ClientRecord[]> {
  const response = await apiClient.get<ApiEnvelope<{ clients: ClientRecord[] }>>("clients/");
  return response.data.clients;
}

export async function getClient(clientId: number): Promise<ClientRecord> {
  const response = await apiClient.get<ApiEnvelope<{ client: ClientRecord }>>(`clients/${clientId}/`);
  return response.data.client;
}

export async function createClient(input: ClientInput): Promise<ClientRecord> {
  const response = await apiClient.post<ApiEnvelope<{ client: ClientRecord }>>("clients/", input, { headers: await csrfHeaders() });
  return response.data.client;
}

export async function updateClient(clientId: number, input: ClientInput): Promise<ClientRecord> {
  const response = await apiClient.put<ApiEnvelope<{ client: ClientRecord }>>(`clients/${clientId}/`, input, { headers: await csrfHeaders() });
  return response.data.client;
}

export async function deleteClient(clientId: number): Promise<void> {
  await apiClient.delete<ApiEnvelope<{ message: string }>>(`clients/${clientId}/`, { headers: await csrfHeaders() });
}
