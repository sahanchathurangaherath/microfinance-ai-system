import axios from "axios";
import Cookies from "js-cookie";

const api = axios.create({
  baseURL: "http://localhost:8000/api/",
  headers: { "Content-Type": "application/json" },
});

// Request interceptor: attach JWT
api.interceptors.request.use((config) => {
  const token = Cookies.get("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
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

        const { data } = await axios.post("/api/auth/token/refresh/", {
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
  getRoles: () => api.get("auth/roles/"),
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
    api.get(`loans/applications/${id}/status-history/`),
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
    api.get("approvals/", { params }),
  getApproval: (id: number) => api.get(`approvals/${id}/`),
  riskDecision: (id: number, data: Record<string, unknown>) =>
    api.post(`approvals/${id}/risk-decision/`, data),
  managerDecision: (id: number, data: Record<string, unknown>) =>
    api.post(`approvals/${id}/manager-decision/`, data),
  committeeDecision: (id: number, data: Record<string, unknown>) =>
    api.post(`approvals/${id}/committee-vote/`, data),
};

// ─── Repayments API ──────────────────────────────────────
export const repaymentsAPI = {
  getRepayments: (params?: Record<string, string>) =>
    api.get("repayments/", { params }),
  recordPayment: (data: Record<string, unknown>) =>
    api.post("repayments/", data),
};

// ─── Collections API ─────────────────────────────────────
export const collectionsAPI = {
  getCollections: (params?: Record<string, string>) =>
    api.get("collections/overdue/", { params }),
  logAction: (data: Record<string, unknown>) =>
    api.post("collections/actions/", data),
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
  getPortfolio: () => api.get("reports/portfolio/"),
  exportCSV: (reportType: string) =>
    api.get("reports/export/", { params: { type: reportType, export_format: "csv" }, responseType: "blob" }),
};

// ─── Audit API ───────────────────────────────────────────
export const auditAPI = {
  getLogs: (params?: Record<string, string>) =>
    api.get("audit/", { params }),
  getLoginAttempts: (params?: Record<string, string>) =>
    api.get("audit/login-attempts/", { params }),
  getPermissionChanges: (params?: Record<string, string>) =>
    api.get("audit/permission-changes/", { params }),
};

// ─── Notifications API ───────────────────────────────────
export const notificationsAPI = {
  getNotifications: (params?: Record<string, string>) =>
    api.get("notifications/", { params }),
  markRead: (id: number) => api.patch(`notifications/${id}/read/`),
  markAllRead: () => api.post("notifications/mark-all-read/"),
};

// ─── KYC API ─────────────────────────────────────────────
export const kycAPI = {
  getKYC: (params?: Record<string, string>) =>
    api.get("kyc/", { params }),
  verifyKYC: (id: number, data: Record<string, unknown>) =>
    api.patch(`kyc/${id}/verify/`, data),
};

// SWR fetcher
export const fetcher = (url: string) =>
  api.get(url).then((res) => res.data);

export default api;