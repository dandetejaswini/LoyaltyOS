import {
  LoyaltyAccount,
  Tier,
  TransactionHistoryPage,
  PointsLot,
  Reward,
  Redemption,
  ReconciliationReport,
  Order,
  OrderReturn,
} from '@/types/loyalty';
import {
  AnomalyDetail,
  AnomalyListPage,
  DetectionRunResponse,
  IntelligenceSummary,
  EngineEvaluationResponse,
} from '@/types/intelligence';
import {
  CorrectiveAction,
  CorrectiveActionListPage,
  InvestigationDetail,
} from '@/types/remediation';

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

export interface LoyaltyAccountSummary {
  account_id: string;
  tier_id: string;
  current_balance: number;
  lifetime_accrued: number;
  lifetime_redeemed: number;
  qualifying_spend: string | number;
  status: string;
}

export interface CustomerSummary {
  customer_id: string;
  email: string;
  first_name: string;
  last_name: string;
  status: string;
  loyalty_account?: LoyaltyAccountSummary;
}

export interface UserProfileResponse {
  id: string;
  email: string;
  full_name?: string;
  role: 'CUSTOMER' | 'OPERATOR' | 'ANALYST' | 'OPERATIONS_MANAGER';
  is_active: boolean;
  customer?: CustomerSummary;
  created_at: string;
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
  private authToken: string | null = null;

  constructor() {
    const envUrl = import.meta.env.VITE_API_BASE_URL;
    if (envUrl) {
      this.baseUrl = envUrl;
    } else if (typeof window !== 'undefined' && window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
      // In production deployment (e.g. Vercel), route via relative same-origin /api/v1
      this.baseUrl = '/api/v1';
    } else {
      this.baseUrl = 'http://localhost:8000/api/v1';
    }
  }

  public setAuthToken(token: string | null) {
    this.authToken = token;
  }

  public getAuthToken(): string | null {
    return this.authToken;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;

    const headers = new Headers(options.headers || {});
    if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
      headers.set('Content-Type', 'application/json');
    }
    headers.set('Accept', 'application/json');
    if (this.authToken && !headers.has('Authorization')) {
      headers.set('Authorization', `Bearer ${this.authToken}`);
    }

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

  // --- System Health & Profile ---
  public async getHealth(): Promise<HealthResponse> {
    return this.get<HealthResponse>('/health');
  }

  public async getMyProfile(): Promise<UserProfileResponse> {
    return this.get<UserProfileResponse>('/auth/me');
  }

  public async syncIdentity(provider: string, idToken: string): Promise<{ user: UserProfileResponse; message: string }> {
    return this.post<{ user: UserProfileResponse; message: string }>('/auth/sync', { provider, id_token: idToken });
  }

  // --- Phase 4: Loyalty Accounts & Customers ---
  public async getMyAccount(): Promise<LoyaltyAccount> {
    return this.get<LoyaltyAccount>('/accounts/me');
  }

  public async getAccount(accountId: string): Promise<LoyaltyAccount> {
    return this.get<LoyaltyAccount>(`/accounts/${accountId}`);
  }

  public async provisionAccount(data: {
    customer_id?: string;
    email: string;
    first_name: string;
    last_name: string;
    phone?: string;
  }): Promise<{ customer: CustomerSummary; account: LoyaltyAccountSummary }> {
    return this.post('/accounts/provision', data);
  }

  // --- Phase 4: Orders & Accruals ---
  public async accrueOrder(data: {
    order_id?: string;
    customer_id: string;
    gross_amount: number;
    tax_amount?: number;
    shipping_amount?: number;
    discount_amount?: number;
    lines: Array<{
      line_number: number;
      sku: string;
      product_name: string;
      category: string;
      quantity: number;
      unit_price: number;
      item_discount?: number;
      is_eligible?: boolean;
    }>;
    idempotency_key?: string;
  }): Promise<{
    order: Order;
    points_earned: number;
    transaction_id: string;
    account_balance_after: number;
  }> {
    return this.post('/orders/accrue', data);
  }

  public async getOrder(orderId: string): Promise<Order> {
    return this.get<Order>(`/orders/${orderId}`);
  }

  // --- Phase 4: Ledger History & Reconciliation ---
  public async getLedgerHistory(
    accountId: string,
    page = 1,
    pageSize = 20,
    entryType?: string
  ): Promise<TransactionHistoryPage> {
    const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) });
    if (entryType) params.append('entry_type', entryType);
    return this.get<TransactionHistoryPage>(`/ledger/accounts/${accountId}/history?${params.toString()}`);
  }

  public async getAccountLots(accountId: string, status?: string): Promise<PointsLot[]> {
    const params = status ? `?status=${encodeURIComponent(status)}` : '';
    return this.get<PointsLot[]>(`/ledger/accounts/${accountId}/lots${params}`);
  }

  public async getReconciliation(accountId: string): Promise<ReconciliationReport> {
    return this.get<ReconciliationReport>(`/ledger/accounts/${accountId}/reconciliation`);
  }

  // --- Phase 4: Rewards & Redemptions ---
  public async getRewards(): Promise<Reward[]> {
    return this.get<Reward[]>('/redemptions/rewards');
  }

  public async redeemReward(data: {
    account_id: string;
    reward_id: string;
    idempotency_key?: string;
  }): Promise<Redemption> {
    return this.post<Redemption>('/redemptions/redeem', data);
  }

  // --- Phase 4: Returns ---
  public async processReturn(data: {
    order_id: string;
    return_type: 'FULL' | 'PARTIAL';
    total_refund_amount: number;
    lines?: Array<{
      order_line_id: string;
      quantity_returned: number;
      refund_amount: number;
    }>;
    idempotency_key?: string;
  }): Promise<OrderReturn> {
    return this.post<OrderReturn>('/returns/process', data);
  }

  // --- Phase 4: Tiers ---
  public async getTiers(): Promise<Tier[]> {
    return this.get<Tier[]>('/tiers');
  }

  public async evaluateTier(accountId: string): Promise<{
    account_id: string;
    previous_tier_id: string;
    new_tier_id: string;
    qualifying_spend: number | string;
    upgraded: boolean;
  }> {
    return this.post(`/tiers/accounts/${accountId}/evaluate`);
  }

  // --- Phase 5: LLIRE Intelligence Engine ---
  public async runDetection(data?: {
    account_id?: string;
    include_detectors?: string[];
  }): Promise<DetectionRunResponse> {
    return this.post<DetectionRunResponse>('/intelligence/detect', data || {});
  }

  public async runSingleDetector(
    detectorName: string,
    accountId?: string
  ): Promise<DetectionRunResponse> {
    const params = accountId ? `?account_id=${encodeURIComponent(accountId)}` : '';
    return this.post<DetectionRunResponse>(`/intelligence/detect/${encodeURIComponent(detectorName)}${params}`);
  }

  public async getAnomalies(params?: {
    category?: string;
    severity?: string;
    status?: string;
    page?: number;
    pageSize?: number;
  }): Promise<AnomalyListPage> {
    const q = new URLSearchParams();
    if (params?.category) q.append('category', params.category);
    if (params?.severity) q.append('severity', params.severity);
    if (params?.status) q.append('status', params.status);
    if (params?.page) q.append('page', String(params.page));
    if (params?.pageSize) q.append('page_size', String(params.pageSize));
    const qs = q.toString();
    return this.get<AnomalyListPage>(`/intelligence/anomalies${qs ? `?${qs}` : ''}`);
  }

  public async getAnomalyDetail(anomalyId: string): Promise<AnomalyDetail> {
    return this.get<AnomalyDetail>(`/intelligence/anomalies/${encodeURIComponent(anomalyId)}`);
  }

  public async getIntelligenceSummary(): Promise<IntelligenceSummary> {
    return this.get<IntelligenceSummary>('/intelligence/summary');
  }

  public async getEvaluation(): Promise<EngineEvaluationResponse> {
    return this.get<EngineEvaluationResponse>('/intelligence/evaluate');
  }

  // --- Phase 6: Remediation & Dual-Key Approval Engine ---
  public async getFindingsAwaitingInvestigation(params?: {
    status?: string;
    page?: number;
    pageSize?: number;
  }): Promise<AnomalyDetail[]> {
    const q = new URLSearchParams();
    if (params?.status) q.append('status', params.status);
    if (params?.page) q.append('page', String(params.page));
    if (params?.pageSize) q.append('page_size', String(params.pageSize));
    const qs = q.toString();
    return this.get<AnomalyDetail[]>(`/corrective-actions/findings-awaiting-investigation${qs ? `?${qs}` : ''}`);
  }

  public async getInvestigationDetail(incidentId: string): Promise<InvestigationDetail> {
    return this.get<InvestigationDetail>(`/corrective-actions/investigations/${encodeURIComponent(incidentId)}`);
  }

  public async startInvestigation(
    incidentId: string,
    data?: { investigator_id?: string; notes?: string }
  ): Promise<InvestigationDetail> {
    return this.post<InvestigationDetail>(`/corrective-actions/investigations/${encodeURIComponent(incidentId)}/start`, data || {});
  }

  public async addInvestigationNote(incidentId: string, note: string): Promise<InvestigationDetail> {
    return this.post<InvestigationDetail>(`/corrective-actions/investigations/${encodeURIComponent(incidentId)}/notes`, { note });
  }

  public async proposeCorrectiveAction(
    incidentId: string,
    data: {
      action_type: string;
      proposed_points?: number;
      reason: string;
      evidence_references?: Record<string, any>;
    }
  ): Promise<CorrectiveAction> {
    return this.post<CorrectiveAction>(`/corrective-actions/investigations/${encodeURIComponent(incidentId)}/propose`, data);
  }

  public async getPendingApprovals(params?: { page?: number; pageSize?: number }): Promise<CorrectiveActionListPage> {
    const q = new URLSearchParams();
    if (params?.page) q.append('page', String(params.page));
    if (params?.pageSize) q.append('page_size', String(params.pageSize));
    const qs = q.toString();
    return this.get<CorrectiveActionListPage>(`/corrective-actions/pending-approvals${qs ? `?${qs}` : ''}`);
  }

  public async reviewProposal(
    incidentId: string,
    data: {
      decision: 'APPROVED' | 'REJECTED';
      notes?: string;
      rejection_reason?: string;
      execute_immediately?: boolean;
    }
  ): Promise<CorrectiveAction> {
    return this.post<CorrectiveAction>(`/corrective-actions/investigations/${encodeURIComponent(incidentId)}/review`, data);
  }

  public async executeCorrection(incidentId: string): Promise<CorrectiveAction> {
    return this.post<CorrectiveAction>(`/corrective-actions/investigations/${encodeURIComponent(incidentId)}/execute`);
  }

  public async getCorrectiveActionHistory(params?: { page?: number; pageSize?: number }): Promise<CorrectiveActionListPage> {
    const q = new URLSearchParams();
    if (params?.page) q.append('page', String(params.page));
    if (params?.pageSize) q.append('page_size', String(params.pageSize));
    const qs = q.toString();
    return this.get<CorrectiveActionListPage>(`/corrective-actions/history${qs ? `?${qs}` : ''}`);
  }
}

export const apiClient = new ApiClient();
