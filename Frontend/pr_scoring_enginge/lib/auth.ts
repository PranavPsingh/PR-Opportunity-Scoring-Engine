import { ApiEnvelope, apiClient } from "@/lib/api/client";

export type AuthenticatedUser = {
  id: number;
  name: string;
  email: string;
  role: "consultant" | "admin";
};

export type ManagedUser = AuthenticatedUser;

type UserResponse = ApiEnvelope<{ user: AuthenticatedUser }>;
type CsrfResponse = ApiEnvelope<{ csrfToken: string }>;

async function csrfHeaders(): Promise<HeadersInit> {
  const response = await apiClient.get<CsrfResponse>("auth/csrf/");
  return { "X-CSRFToken": response.data.csrfToken };
}

export async function getCurrentUser(): Promise<AuthenticatedUser> {
  const response = await apiClient.get<UserResponse>("auth/me/");
  return response.data.user;
}

export async function signIn(email: string, password: string): Promise<AuthenticatedUser> {
  const response = await apiClient.post<UserResponse>("auth/login/", { email, password }, { headers: await csrfHeaders() });
  return response.data.user;
}

export async function signOut(): Promise<void> {
  await apiClient.post<ApiEnvelope<{ message: string }>>("auth/logout/", {}, { headers: await csrfHeaders() });
}

export async function getUsers(): Promise<ManagedUser[]> {
  const response = await apiClient.get<ApiEnvelope<{ users: ManagedUser[] }>>("auth/users/");
  return response.data.users;
}

export async function updateUserRole(userId: number, role: ManagedUser["role"]): Promise<ManagedUser> {
  const response = await apiClient.post<ApiEnvelope<{ user: ManagedUser }>>(
    `auth/users/${userId}/role/`, { role }, { headers: await csrfHeaders() },
  );
  return response.data.user;
}

export async function removeUser(userId: number): Promise<void> {
  await apiClient.post<ApiEnvelope<{ message: string }>>(
    `auth/users/${userId}/delete/`, {}, { headers: await csrfHeaders() },
  );
}
