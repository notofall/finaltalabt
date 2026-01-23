/**
 * API Utility Layer
 * Unified API interface for both V1 (pg) and V2 endpoints
 * Enables gradual migration from V1 to V2 APIs
 */
import axios from "axios";
import { BACKEND_URL, API_URL as API_V1, API_V2_URL as API_V2 } from "../config/api";

const BASE_URL = BACKEND_URL;

/**
 * Create axios instance with default config
 */
const createApiClient = (baseURL) => {
  const client = axios.create({ baseURL });
  return client;
};

const v1Client = createApiClient(API_V1);
const v2Client = createApiClient(API_V2);

/**
 * Get auth headers
 */
const getHeaders = (token) => ({
  Authorization: `Bearer ${token}`,
  "Content-Type": "application/json",
});

// ==================== Projects API ====================

export const projectsApi = {
  /**
   * Get all projects (uses V1 for full data including stats)
   */
  getAll: async (token) => {
    const res = await v1Client.get("/projects", { headers: getHeaders(token) });
    return res.data;
  },

  /**
   * Get active projects only (uses V2)
   */
  getActive: async (token) => {
    const res = await v2Client.get("/projects/active", { headers: getHeaders(token) });
    return res.data;
  },

  /**
   * Get project summary (uses V2)
   */
  getSummary: async (token) => {
    const res = await v2Client.get("/projects/summary", { headers: getHeaders(token) });
    return res.data;
  },

  /**
   * Get single project by ID (uses V2)
   */
  getById: async (token, projectId) => {
    const res = await v2Client.get(`/projects/${projectId}`, { headers: getHeaders(token) });
    return res.data;
  },

  /**
   * Create new project (uses V2)
   */
  create: async (token, projectData) => {
    const res = await v2Client.post("/projects/", projectData, { headers: getHeaders(token) });
    return res.data;
  },

  /**
   * Update project (uses V2)
   */
  update: async (token, projectId, projectData) => {
    const res = await v2Client.put(`/projects/${projectId}`, projectData, { headers: getHeaders(token) });
    return res.data;
  },

  /**
   * Delete project (uses V2)
   */
  delete: async (token, projectId) => {
    await v2Client.delete(`/projects/${projectId}`, { headers: getHeaders(token) });
    return true;
  },
};

// ==================== Orders API ====================

export const ordersApi = {
  /**
   * Get all orders (uses V1 for full data)
   */
  getAll: async (token) => {
    const res = await v1Client.get("/purchase-orders", { headers: getHeaders(token) });
    return res.data;
  },

  /**
   * Get order stats (uses V2)
   */
  getStats: async (token) => {
    const res = await v2Client.get("/orders/stats", { headers: getHeaders(token) });
    return res.data;
  },

  /**
   * Get pending orders (uses V2)
   */
  getPending: async (token) => {
    const res = await v2Client.get("/orders/pending", { headers: getHeaders(token) });
    return res.data;
  },

  /**
   * Get approved orders (uses V2)
   */
  getApproved: async (token) => {
    const res = await v2Client.get("/orders/approved", { headers: getHeaders(token) });
    return res.data;
  },

  /**
   * Get orders pending delivery (uses V2)
   */
  getPendingDelivery: async (token) => {
    const res = await v2Client.get("/orders/pending-delivery", { headers: getHeaders(token) });
    return res.data;
  },

  /**
   * Get orders by project (uses V2)
   */
  getByProject: async (token, projectId) => {
    const res = await v2Client.get(`/orders/by-project/${projectId}`, { headers: getHeaders(token) });
    return res.data;
  },

  /**
   * Approve order (uses V2)
   */
  approve: async (token, orderId) => {
    const res = await v2Client.post(`/orders/${orderId}/approve`, {}, { headers: getHeaders(token) });
    return res.data;
  },

  /**
   * Reject order (uses V2)
   */
  reject: async (token, orderId, reason = "") => {
    const res = await v2Client.post(`/orders/${orderId}/reject`, null, {
      headers: getHeaders(token),
      params: { reason },
    });
    return res.data;
  },
};

// ==================== Suppliers API ====================

export const suppliersApi = {
  /**
   * Get all suppliers (uses V1 for full data)
   */
  getAll: async (token) => {
    const res = await v1Client.get("/suppliers", { headers: getHeaders(token) });
    return res.data;
  },

  /**
   * Get active suppliers (uses V2)
   */
  getActive: async (token) => {
    const res = await v2Client.get("/suppliers/active", { headers: getHeaders(token) });
    return res.data;
  },

  /**
   * Get supplier summary (uses V2)
   */
  getSummary: async (token) => {
    const res = await v2Client.get("/suppliers/summary", { headers: getHeaders(token) });
    return res.data;
  },

  /**
   * Search suppliers (uses V2)
   */
  search: async (token, query) => {
    const res = await v2Client.get("/suppliers/search", {
      headers: getHeaders(token),
      params: { q: query },
    });
    return res.data;
  },

  /**
   * Get supplier by ID (uses V2)
   */
  getById: async (token, supplierId) => {
    const res = await v2Client.get(`/suppliers/${supplierId}`, { headers: getHeaders(token) });
    return res.data;
  },

  /**
   * Create supplier (uses V2)
   */
  create: async (token, supplierData) => {
    const res = await v2Client.post("/suppliers/", supplierData, { headers: getHeaders(token) });
    return res.data;
  },

  /**
   * Update supplier (uses V2)
   */
  update: async (token, supplierId, supplierData) => {
    const res = await v2Client.put(`/suppliers/${supplierId}`, supplierData, { headers: getHeaders(token) });
    return res.data;
  },

  /**
   * Delete supplier (uses V2)
   */
  delete: async (token, supplierId) => {
    await v2Client.delete(`/suppliers/${supplierId}`, { headers: getHeaders(token) });
    return true;
  },
};

// ==================== Requests API ====================

export const requestsApi = {
  /**
   * Get all requests (uses V1 for full data)
   */
  getAll: async (token) => {
    const res = await v1Client.get("/requests", { headers: getHeaders(token) });
    return res.data;
  },

  /**
   * Get request stats (uses V2)
   */
  getStats: async (token) => {
    const res = await v2Client.get("/requests/stats", { headers: getHeaders(token) });
    return res.data;
  },

  /**
   * Get pending requests (uses V2)
   */
  getPending: async (token) => {
    const res = await v2Client.get("/requests/pending", { headers: getHeaders(token) });
    return res.data;
  },

  /**
   * Get requests by status (uses V2)
   */
  getByStatus: async (token, status) => {
    const res = await v2Client.get(`/requests/by-status/${status}`, { headers: getHeaders(token) });
    return res.data;
  },

  /**
   * Get requests by project (uses V2)
   */
  getByProject: async (token, projectId) => {
    const res = await v2Client.get(`/requests/by-project/${projectId}`, { headers: getHeaders(token) });
    return res.data;
  },

  /**
   * Approve request (uses V2)
   */
  approve: async (token, requestId) => {
    const res = await v2Client.post(`/requests/${requestId}/approve`, {}, { headers: getHeaders(token) });
    return res.data;
  },

  /**
   * Reject request (uses V2)
   */
  reject: async (token, requestId, reason = "") => {
    const res = await v2Client.post(`/requests/${requestId}/reject`, null, {
      headers: getHeaders(token),
      params: { reason },
    });
    return res.data;
  },
};

// ==================== Delivery API ====================

export const deliveryApi = {
  /**
   * Get delivery stats (uses V2)
   */
  getStats: async (token) => {
    const res = await v2Client.get("/delivery/stats", { headers: getHeaders(token) });
    return res.data;
  },

  /**
   * Get pending deliveries (uses V2)
   */
  getPending: async (token) => {
    const res = await v2Client.get("/delivery/pending", { headers: getHeaders(token) });
    return res.data;
  },

  /**
   * Mark order as shipped (uses V2)
   */
  markAsShipped: async (token, orderId, trackingNumber = "") => {
    const res = await v2Client.post(`/delivery/${orderId}/ship`, null, {
      headers: getHeaders(token),
      params: { tracking_number: trackingNumber },
    });
    return res.data;
  },

  /**
   * Confirm receipt (uses V2)
   */
  confirmReceipt: async (token, orderId, items) => {
    const res = await v2Client.post(
      `/delivery/${orderId}/confirm-receipt`,
      { items },
      { headers: getHeaders(token) }
    );
    return res.data;
  },

  /**
   * Get project supply status (uses V2)
   */
  getProjectSupplyStatus: async (token, projectId) => {
    const res = await v2Client.get(`/delivery/project/${projectId}/supply-status`, { headers: getHeaders(token) });
    return res.data;
  },
};

// ==================== Legacy V1 APIs (no V2 equivalent yet) ====================

export const legacyApi = {
  // Auth
  login: async (email, password) => {
    const res = await v1Client.post("/auth/login", { email, password });
    return res.data;
  },

  getMe: async (token) => {
    const res = await v1Client.get("/auth/me", { headers: getHeaders(token) });
    return res.data;
  },

  register: async (data) => {
    const res = await v1Client.post("/auth/register", data);
    return res.data;
  },

  // Budget
  getBudgetCategories: async (token) => {
    const res = await v1Client.get("/budget-categories", { headers: getHeaders(token) });
    return res.data;
  },

  // Price Catalog
  getPriceCatalog: async (token, params) => {
    const res = await v1Client.get("/price-catalog", {
      headers: getHeaders(token),
      params,
    });
    return res.data;
  },

  // Reports
  getDashboardReports: async (token) => {
    const res = await v1Client.get("/reports/dashboard", { headers: getHeaders(token) });
    return res.data;
  },

  // Settings
  getSettings: async (token) => {
    const res = await v1Client.get("/settings", { headers: getHeaders(token) });
    return res.data;
  },

  // Users
  getUsersList: async (token) => {
    const res = await v1Client.get("/users/list", { headers: getHeaders(token) });
    return res.data;
  },
};

// Export API URLs for direct use when needed
export { API_V1, API_V2, BASE_URL };

// Default export
export default {
  projects: projectsApi,
  orders: ordersApi,
  suppliers: suppliersApi,
  requests: requestsApi,
  delivery: deliveryApi,
  legacy: legacyApi,
  API_V1,
  API_V2,
};
