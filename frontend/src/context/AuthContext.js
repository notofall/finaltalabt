import { createContext, useContext, useState, useEffect } from "react";
import axios from "axios";

const AuthContext = createContext(null);

// Auto-detect backend URL based on current location
const getBackendUrl = () => {
  // If env variable is set and we're on that domain, use it
  if (process.env.REACT_APP_BACKEND_URL) {
    // Check if we're on the preview domain
    if (window.location.hostname.includes('preview.emergentagent.com')) {
      return process.env.REACT_APP_BACKEND_URL;
    }
    // Check if we're on localhost (development)
    if (window.location.hostname === 'localhost') {
      return process.env.REACT_APP_BACKEND_URL;
    }
  }
  // Otherwise, use the current origin (for production deployment)
  return window.location.origin;
};

const BACKEND_URL = getBackendUrl();

// Legacy PostgreSQL APIs (v1) - للتوافق مع الكود القديم
const API_URL = `${BACKEND_URL}/api/pg`;

// New V2 APIs with Service/Repository pattern - الموصى به
const API_V2_URL = `${BACKEND_URL}/api/v2`;

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem("token"));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const initAuth = async () => {
      const savedToken = localStorage.getItem("token");
      if (savedToken) {
        try {
          // Using V2 Auth API
          const response = await axios.get(`${API_V2_URL}/auth/me`, {
            headers: { Authorization: `Bearer ${savedToken}` },
          });
          setUser(response.data);
          setToken(savedToken);
        } catch (error) {
          localStorage.removeItem("token");
          setToken(null);
          setUser(null);
        }
      }
      setLoading(false);
    };

    initAuth();
  }, []);

  const login = async (email, password) => {
    // Using V2 Auth API
    const response = await axios.post(`${API_V2_URL}/auth/login`, {
      email,
      password,
    });
    const { access_token, user: userData } = response.data;
    localStorage.setItem("token", access_token);
    setToken(access_token);
    setUser(userData);
    return userData;
  };

  const register = async (name, email, password, role) => {
    // Still using V1 for register (not in V2 yet)
    const response = await axios.post(`${API_URL}/auth/register`, {
      name,
      email,
      password,
      role,
    });
    const { access_token, user: userData } = response.data;
    localStorage.setItem("token", access_token);
    setToken(access_token);
    setUser(userData);
    return userData;
  };

  const changePassword = async (currentPassword, newPassword) => {
    // Using V2 Auth API
    const response = await axios.post(
      `${API_V2_URL}/auth/change-password`,
      { current_password: currentPassword, new_password: newPassword },
      { headers: { Authorization: `Bearer ${token}` } }
    );
    return response.data;
  };

  const logout = () => {
    localStorage.removeItem("token");
    setToken(null);
    setUser(null);
  };

  const getAuthHeaders = () => ({
    headers: { Authorization: `Bearer ${token}` },
  });

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        login,
        register,
        logout,
        changePassword,
        getAuthHeaders,
        API_URL,
        API_V2_URL,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
