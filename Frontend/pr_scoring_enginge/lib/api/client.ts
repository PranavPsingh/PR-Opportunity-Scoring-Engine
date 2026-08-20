export type ApiErrorPayload = {
  code?: string;
  message?: string;
};

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly code?: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

type ApiClientOptions = {
  baseUrl?: string;
  getAccessToken?: () => string | null | Promise<string | null>;
};

const defaultBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

export class ApiClient {
  private readonly baseUrl: string;
  private readonly getAccessToken?: ApiClientOptions["getAccessToken"];

  constructor({ baseUrl = defaultBaseUrl, getAccessToken }: ApiClientOptions = {}) {
    this.baseUrl = baseUrl.replace(/\/$/, "");
    this.getAccessToken = getAccessToken;
  }

  async get<T>(path: string, init?: RequestInit): Promise<T> {
    return this.request<T>(path, { ...init, method: "GET" });
  }

  async request<T>(path: string, init: RequestInit = {}): Promise<T> {
    const headers = new Headers(init.headers);
    headers.set("Accept", "application/json");

    if (init.body && !headers.has("Content-Type")) {
      headers.set("Content-Type", "application/json");
    }

    const token = await this.getAccessToken?.();
    if (token) headers.set("Authorization", `Bearer ${token}`);

    let response: Response;
    try {
      response = await fetch(`${this.baseUrl}/${path.replace(/^\//, "")}`, {
        ...init,
        headers,
      });
    } catch {
      throw new ApiError("Unable to reach the API.", 0, "network_error");
    }

    const body = await parseJson(response);
    if (!response.ok) {
      const error = isApiErrorResponse(body) ? body.error : undefined;
      throw new ApiError(error?.message ?? "The API request failed.", response.status, error?.code);
    }

    return body as T;
  }
}

async function parseJson(response: Response): Promise<unknown> {
  const contentType = response.headers.get("content-type") ?? "";
  if (!contentType.includes("application/json")) return undefined;
  return response.json();
}

function isApiErrorResponse(value: unknown): value is { error?: ApiErrorPayload } {
  return typeof value === "object" && value !== null && "error" in value;
}

export const apiClient = new ApiClient();
