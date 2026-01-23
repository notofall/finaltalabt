/**
 * API Configuration - Auto-detect backend URL
 * يكتشف تلقائياً عنوان الخادم بناءً على موقع التشغيل
 */

// Auto-detect backend URL based on current location
export const getBackendUrl = () => {
  // If we're on the preview domain (Emergent)
  if (window.location.hostname.includes('preview.emergentagent.com')) {
    return process.env.REACT_APP_BACKEND_URL || window.location.origin;
  }
  
  // If we're on localhost (development)
  if (window.location.hostname === 'localhost') {
    return process.env.REACT_APP_BACKEND_URL || window.location.origin;
  }
  
  // Production: use the current origin (same server)
  return window.location.origin;
};

export const BACKEND_URL = getBackendUrl();

// API URLs
export const API_URL = `${BACKEND_URL}/api/pg`;
export const API_V2_URL = `${BACKEND_URL}/api/v2`;

export default {
  BACKEND_URL,
  API_URL,
  API_V2_URL,
  getBackendUrl
};
