import axios from "axios";
import Cookies from "js-cookie";

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_BASE_URL || "/api",
  headers: { "Content-Type": "application/json" },
});

// Request interceptor: attach JWT and normalize relative URLs
api.interceptors.request.use((config) => {
  const token = Cookies.get("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  if (config.url && config.url.startsWith("/") && !config.url.startsWith("//")) {
    config.url = config.url.slice(1);
  }

  return config;
});

// Response interceptor: handle 401 with token refresh
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value: unknown) => void;
  reject: (reason: unknown) => void;
}> = [];

const processQueue = (error: unknown, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) prom.reject(error);
    else prom.resolve(token);
  });
  failedQueue = [];
};

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then((token) => {
          originalRequest.headers.Authorization = `Bearer ${token}`;
          return api(originalRequest);
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const refreshToken = Cookies.get("refresh_token");
        if (!refreshToken) throw new Error("No refresh token");

        const { data } = await axios.post("/api/auth/refresh/", {
          refresh: refreshToken,
        });

        Cookies.set("access_token", data.access, { sameSite: "Strict" });
        originalRequest.headers.Authorization = `Bearer ${data.access}`;
        processQueue(null, data.access);
        return api(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        Cookies.remove("access_token");
        Cookies.remove("refresh_token");
        Cookies.remove("user_role");
        if (typeof window !== "undefined") {
          window.location.href = "/login";
        }
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }
    return Promise.reject(error);
  }
);

// ─── Auth API ────────────────────────────────────────────
export const authAPI = {
  login: (username: string, password: string) =>
    api.post("auth/login/", { username, password }),
  logout: (refresh: string) => api.post("auth/logout/", { refresh }),
  getCurrentUser: () => api.get("auth/me/"),
  forgotPassword: (email: string) => api.post("auth/forgot-password/", { email }),
  resetPassword: (data: {
    uid: string;
    token: string;
    new_password: string;
    confirm_password: string;
  }) => api.post("auth/reset-password/", data),
  changePassword: (data: {
    old_password: string;
    new_password: string;
  }) => api.post("auth/change-password/", data),
};

// ─── Users API ───────────────────────────────────────────
export const usersAPI = {
  getUsers: (params?: Record<string, string>) =>
    api.get("users/", { params }),
  getUser: (id: number) => api.get(`users/${id}/`),
  createUser: (data: Record<string, unknown>) => api.post("users/", data),
  updateUser: (id: number, data: Record<string, unknown>) =>
    api.patch(`users/${id}/`, data),
  deleteUser: (id: number) => api.delete(`users/${id}/`),
  getRoles: () => api.get("users/roles/"),
  getUserActivity: (userId: number) =>
    api.get(`users/${userId}/activity/`),
};

// ─── Clients API ─────────────────────────────────────────
export const clientsAPI = {
  getClients: (params?: Record<string, string>) =>
    api.get("clients/", { params }),
  getClient: (id: number) => api.get(`clients/${id}/`),
  createClient: (data: Record<string, unknown>) =>
    api.post("clients/", data),
  updateClient: (id: number, data: Record<string, unknown>) =>
    api.patch(`clients/${id}/`, data),
};

// ─── Loans API ───────────────────────────────────────────
export const loansAPI = {
  getApplications: (params?: Record<string, string>) =>
    api.get("loans/applications/", { params }),
  getApplication: (id: number) => api.get(`loans/applications/${id}/`),
  createApplication: (data: Record<string, unknown>) =>
    api.post("loans/applications/", data),
  updateApplication: (id: number, data: Record<string, unknown>) =>
    api.patch(`loans/applications/${id}/`, data),
  getProducts: () => api.get("loans/products/"),
  getStatusHistory: (id: number) =>
    api.get(`loans/applications/${id}/status/`),
  submitCashflow: (id: number, data: Record<string, unknown>) =>
    api.post(`loans/applications/${id}/cashflow/`, data),
  uploadDocument: (id: number, formData: FormData) =>
    api.post(`loans/applications/${id}/documents/`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    }),
};

// ─── Approvals API 
export const approvalsAPI = {
  getApprovals: (params?: Record<string, string>) =>
    api.get("approvals/pending/", { params }),
  getRiskReview: () => api.get("approvals/pending/risk-review/"),
  getManagerReview: () => api.get("approvals/pending/manager-review/"),
  getCommitteeReview: () => api.get("approvals/pending/committee/"),
  riskDecision: (loanId: number, data: Record<string, unknown>) =>
    api.post(`approvals/${loanId}/risk-decision/`, data),
  managerDecision: (loanId: number, data: Record<string, unknown>) =>
    api.post(`approvals/${loanId}/manager-decision/`, data),
  committeeDecision: (loanId: number, data: Record<string, unknown>) =>
    api.post(`approvals/${loanId}/committee-vote/`, data),
  getHistory: (loanId: number) =>
    api.get(`approvals/${loanId}/history/`),
};

// ─── Repayments API ──────────────────────────────────────
export const repaymentsAPI = {
  getRepayments: (params?: Record<string, string>) =>
    api.get("repayments/", { params }),
  recordPayment: (data: Record<string, unknown>) =>
    api.post("repayments/payments/", data),
};

// ─── Collections API ─────────────────────────────────────
export const collectionsAPI = {
  getCollections: (params?: Record<string, string>) =>
    api.get("collections/overdue/", { params }),
  
  assignCase: (caseId: number, data: Record<string, unknown>) =>
    api.post(`collections/${caseId}/assign/`, data),
  
  logContact: (caseId: number, data: Record<string, unknown>) =>
    api.post(`collections/${caseId}/contact/`, data),
  
  recordPromiseToPay: (caseId: number, data: Record<string, unknown>) =>
    api.post(`collections/${caseId}/promise-to-pay/`, data),
  
  escalateCase: (caseId: number, data: Record<string, unknown>) =>
    api.post(`collections/${caseId}/escalate/`, data),
  
  resolveCase: (caseId: number, data: Record<string, unknown>) =>
    api.post(`collections/${caseId}/resolve/`, data),
};

// ─── Fraud API ───────────────────────────────────────────
export const fraudAPI = {
  getAlerts: (params?: Record<string, string>) =>
    api.get("fraud/alerts/", { params }),
  resolveAlert: (id: number, data: Record<string, unknown>) =>
    api.patch(`fraud/alerts/${id}/close/`, data),
};

// ─── Reports API ─────────────────────────────────────────
export const reportsAPI = {
  getDashboard: () => api.get("reports/dashboard/"),
  getPortfolio: () => api.get("reports/dashboard/portfolio/"),
  exportCSV: (reportType: string) =>
    api.get("reports/export/", { params: { type: reportType, export_format: "csv" }, responseType: "blob" }),
  exportJSON: (reportType: string) =>
    api.get("reports/export/", { params: { type: reportType, export_format: "export_json" } }),
};

// ─── Audit API ───────────────────────────────────────────
export const auditAPI = {
  getLogs: (params?: Record<string, string>) =>
    api.get("audit/logs/", { params }),
  getLoginAttempts: (params?: Record<string, string>) =>
    api.get("audit/login-attempts/", { params }),
  getPermissionChanges: (params?: Record<string, string>) =>
    api.get("audit/decisions/", { params }),
  getAgentConfigs: () =>
    api.get("audit/agent-config/"),
  updateAgentConfig: (agentId: string, data: Record<string, unknown>) =>
    api.patch(`audit/agent-config/${agentId}/`, data),
  getAgentPerformance: (agentId: string, params?: Record<string, unknown>) =>
    api.get(`audit/agent-performance/${agentId}/`, { params }),
  getAgentConfigChangeLogs: () =>
    api.get("audit/agent-config-logs/"),
  getAIHealth: () =>
    api.get("audit/ai/health/"),
  enableManualMode: () =>
    api.post("audit/system/manual-mode/enable/"),
  disableManualMode: () =>
    api.post("audit/system/manual-mode/disable/"),
  getIncidents: () =>
    api.get("audit/system/incidents/"),
  resolveIncident: (id: number) =>
    api.post(`audit/system/incidents/${id}/resolve/`),
  getManualReviewQueue: () =>
    api.get("audit/system/manual-review/"),
  submitManualReview: (caseId: number, data: Record<string, unknown>) =>
    api.post(`audit/system/manual-review/${caseId}/submit/`, data),
  retryAIRequest: (caseId: number) =>
    api.post(`audit/system/manual-review/${caseId}/retry/`),
};

// ─── Notifications API ───────────────────────────────────
export const notificationsAPI = {
  getNotifications: (params?: Record<string, string>) =>
    api.get("notifications/", { params }),
  markRead: (id: number) => api.patch(`notifications/${id}/read/`),
  markAllRead: () => api.post("notifications/mark-all-read/"),
  // Staff workflow endpoints (SMS/Email to clients)
  getQueue: () => api.get("notifications/queue/"),
  getPendingDrafts: () => api.get("notifications/pending/"),
  approveDraft: (id: number) => api.post(`notifications/${id}/approve/`),
  rejectDraft: (id: number, data: { reason: string }) => api.post(`notifications/${id}/reject/`, data),
  sendDraft: (id: number) => api.post(`notifications/${id}/send/`),
};

// ─── KYC API ─────────────────────────────────────────────
export const kycAPI = {
  // Get all clients (KYC records)
  getKYC: (params?: Record<string, string>) =>
    api.get("clients/", { params }),
  
  // Get specific client's KYC data
  getClientKYC: (clientId: number) =>
    api.get(`clients/${clientId}/kyc/`),
  
  // Update/Verify KYC checklist
  verifyKYC: (clientId: number, data: Record<string, unknown>) =>
    api.patch(`clients/${clientId}/kyc/`, data),
  
  // Submit for AI validation
  submitForValidation: (clientId: number) =>
    api.post(`clients/${clientId}/kyc/submit/`, {}),
  
  // Upload KYC documents
  uploadDocument: (clientId: number, formData: FormData) =>
    api.post(`clients/${clientId}/documents/`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    }),
};

// SWR fetcher
export const fetcher = (url: string) =>
  api.get(url).then((res) => res.data);

export default api;