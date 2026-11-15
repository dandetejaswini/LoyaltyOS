export interface ProblemDetails {
  type: string;
  title: string;
  status: number;
  detail?: string;
  instance?: string;
  timestamp: string;
  errors?: Array<{ loc: string[]; msg: string; type: string }>;
}

export interface HealthResponse {
  status: 'healthy' | 'degraded' | 'unhealthy';
  app_name: string;
  version: string;
  environment: string;
  database: {
    status: string;
    connected: boolean;
    provider: string;
    message?: string;
    error?: string;
  };
  timestamp: string;
}

export class ApiError extends Error {
  public problem: ProblemDetails;

  constructor(problem: ProblemDetails) {
    super(problem.detail || problem.title || `API Error ${problem.status}`);
    this.name = 'ApiError';
    this.problem = problem;
  }
}

class ApiClient {
  private baseUrl: string;

  constructor() {
    this.baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
    
    const headers = new Headers(options.headers || {});
    if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
      headers.set('Content-Type', 'application/json');
    }
    headers.set('Accept', 'application/json');

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      if (!response.ok) {
        let problem: ProblemDetails;
        try {
          problem = await response.json();
        } catch {
          problem = {
            type: 'about:blank',
            title: response.statusText || 'HTTP Error',
            status: response.status,
            detail: `Server responded with status code ${response.status}`,
            timestamp: new Date().toISOString(),
          };
        }
        throw new ApiError(problem);
      }

      return await response.json();
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }
      throw new ApiError({
        type: 'https://yottaflex.io/errors/network-error',
        title: 'Network Communication Error',
        status: 0,
        detail: error instanceof Error ? error.message : 'Failed to reach API server.',
        timestamp: new Date().toISOString(),
      });
    }
  }

  public async get<T>(endpoint: string, headers?: Record<string, string>): Promise<T> {
    return this.request<T>(endpoint, { method: 'GET', headers });
  }

  public async post<T>(endpoint: string, body?: unknown, headers?: Record<string, string>): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  public async getHealth(): Promise<HealthResponse> {
    return this.get<HealthResponse>('/health');
  }
}

export const apiClient = new ApiClient();
