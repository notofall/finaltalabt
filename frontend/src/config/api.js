/**
 * API Configuration - Auto-detect backend URL
 * يكتشف تلقائياً عنوان الخادم بناءً على موقع التشغيل
 */

// Validate hostname safely
const isEmergentPreview = () => {
  const hostname = window.location.hostname;
  // 🔒 Security: Use exact match or proper suffix check
  return hostname === 'preview.emergentagent.com' || 
         hostname.endsWith('.preview.emergentagent.com');
};

// Auto-detect backend URL based on current location
export const getBackendUrl = () => {
  // If we're on the preview domain (Emergent)
  if (isEmergentPreview()) {
    return process.env.REACT_APP_BACKEND_URL || window.location.origin;
  }
  
  // If we're on localhost (development)
  if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
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
