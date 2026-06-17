// API Configuration
const configuredApiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

function normalizeApiBaseUrl(url) {
  try {
    const normalized = new URL(url);

    // Vite often binds localhost on IPv6 in Windows while the backend binds IPv4.
    // Normalize the API host to IPv4 to avoid browser fetch failures on ::1.
    if (normalized.hostname === 'localhost') {
      normalized.hostname = '127.0.0.1';
    }

    return normalized.toString().replace(/\/$/, '');
  } catch {
    return url.replace('://localhost', '://127.0.0.1').replace(/\/$/, '');
  }
}

export const API_BASE_URL = normalizeApiBaseUrl(configuredApiBaseUrl);

const ACCESS_TOKEN_KEY = 'auth_token';
const REFRESH_TOKEN_KEY = 'auth_refresh_token';
const USER_KEY = 'auth_user';
const AUTH_ERROR_KEY = 'auth_error';

let refreshPromise = null;

function emitSessionChange() {
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new CustomEvent('auth:session-changed'));
  }
}

function normalizeErrorMessage(detail, fallback = 'Request failed') {
  if (Array.isArray(detail)) {
    return detail[0]?.msg || fallback;
  }

  return detail || fallback;
}

function rememberAuthError(message) {
  if (typeof window !== 'undefined') {
    sessionStorage.setItem(AUTH_ERROR_KEY, message);
  }
}

export function consumeAuthError() {
  if (typeof window === 'undefined') return '';

  const message = sessionStorage.getItem(AUTH_ERROR_KEY) || '';
  sessionStorage.removeItem(AUTH_ERROR_KEY);
  return message;
}

// Helper function to build API URLs
export function apiUrl(path) {
  if (path.startsWith('http://') || path.startsWith('https://')) {
    return path;
  }

  const cleanPath = path.startsWith('/') ? path.slice(1) : path;
  return `${API_BASE_URL}/${cleanPath}`;
}

export function getStoredAccessToken() {
  return typeof window !== 'undefined' ? localStorage.getItem(ACCESS_TOKEN_KEY) : null;
}

export function getStoredRefreshToken() {
  return typeof window !== 'undefined' ? localStorage.getItem(REFRESH_TOKEN_KEY) : null;
}

export function getStoredUser() {
  if (typeof window === 'undefined') return null;

  try {
    return JSON.parse(localStorage.getItem(USER_KEY) || 'null');
  } catch {
    return null;
  }
}

export function storeAuthSession({ accessToken, refreshToken, user } = {}) {
  if (typeof window === 'undefined') return;

  if (accessToken) {
    localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
  }

  if (refreshToken) {
    localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
  }

  if (user !== undefined) {
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  }

  sessionStorage.removeItem(AUTH_ERROR_KEY);
  emitSessionChange();
}

export function clearAuthSession() {
  if (typeof window === 'undefined') return;

  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
  emitSessionChange();
}

async function refreshAccessToken() {
  const refreshToken = getStoredRefreshToken();

  if (!refreshToken) {
    clearAuthSession();
    throw new Error('Session expired. Please sign in again.');
  }

  if (!refreshPromise) {
    refreshPromise = (async () => {
      const response = await fetch(apiUrl('api/v1/auth/refresh'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        clearAuthSession();
        throw new Error(normalizeErrorMessage(error.detail, 'Session expired. Please sign in again.'));
      }

      const data = await response.json();
      storeAuthSession({
        accessToken: data.access_token,
        refreshToken: data.refresh_token,
      });
      return data.access_token;
    })();
  }

  try {
    return await refreshPromise;
  } finally {
    refreshPromise = null;
  }
}

function getRoleLoginPath() {
  try {
    const user = JSON.parse(localStorage.getItem('auth_user') || 'null');
    const roleMap = {
      INDIVIDUAL: '/login/customer',
      VENDOR: '/login/vendor',
      LOGISTIC_MANAGER: '/login/manager',
      WAREHOUSE_MANAGER: '/login/warehouse',
      DISPATCHER: '/login/dispatcher',
      DRIVER: '/login/driver',
      AI_AGENT: '/login',
      AI_SUPPORT: '/login',
      CUSTOMER_SUPPORT: '/login',
    };
    return roleMap[user?.role] || '/login/customer';
  } catch {
    return '/login/customer';
  }
}

function redirectToLogin(message) {
  if (typeof window === 'undefined') return;

  const loginPath = getRoleLoginPath();
  rememberAuthError(message);
  if (!window.location.pathname.startsWith('/login')) {
    window.location.assign(loginPath);
  }
}

export async function authenticatedJsonRequest(path, options = {}) {
  const requestUrl = apiUrl(path);
  const requestHeaders = new Headers(options.headers || {});
  const hasBody = options.body !== undefined && options.body !== null;
  const isFormData = typeof FormData !== 'undefined' && options.body instanceof FormData;

  if (hasBody && !isFormData && !requestHeaders.has('Content-Type')) {
    requestHeaders.set('Content-Type', 'application/json');
  }

  const execute = async (token) => {
    const headers = new Headers(requestHeaders);
    if (token) {
      headers.set('Authorization', `Bearer ${token}`);
    }

    return fetch(requestUrl, {
      ...options,
      headers,
    });
  };

  let response = await execute(getStoredAccessToken());

  if (response.status === 401) {
    try {
      const nextAccessToken = await refreshAccessToken();
      response = await execute(nextAccessToken);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Session expired. Please sign in again.';
      redirectToLogin(message);
      throw new Error(message);
    }
  }

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    const message = normalizeErrorMessage(error.detail, `HTTP ${response.status}`);

    if (response.status === 401) {
      clearAuthSession();
      redirectToLogin(message);
    }

    throw new Error(message);
  }

  if (response.status === 204) return null;
  return response.json();
}

// Axios-like API client for convenience
const apiClient = {
  async get(url, config = {}) {
    const data = await authenticatedJsonRequest(url, {
      method: 'GET',
      ...config,
    });
    return { data };
  },

  async post(url, body, config = {}) {
    const data = await authenticatedJsonRequest(url, {
      method: 'POST',
      body: JSON.stringify(body),
      ...config,
    });
    return { data };
  },

  async put(url, body, config = {}) {
    const data = await authenticatedJsonRequest(url, {
      method: 'PUT',
      body: JSON.stringify(body),
      ...config,
    });
    return { data };
  },

  async delete(url, config = {}) {
    const data = await authenticatedJsonRequest(url, {
      method: 'DELETE',
      ...config,
    });
    return { data };
  },
};

export default apiClient;
