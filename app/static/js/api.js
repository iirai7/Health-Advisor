/**
 * api.js
 * Central fetch wrapper for Smart Diagnosis app.
 *
 * Automatically attaches Authorization header, parses JSON,
 * and handles 401 redirects globally.
 *
 * Exposes a global `API` object used by all other JS files.
 *
 * Usage:
 *   const res = await API.post('/api/auth/login', { email, password });
 *   const res = await API.get('/api/family/');
 *   const res = await API.delete('/api/family/5');
 */

const API = (function () {

    // ─────────────────────────────────────────
    // CONFIG
    // ─────────────────────────────────────────
    const BASE_URL = '';          // same origin — Flask serves both frontend and API
    const TOKEN_KEY = 'token';
    const LOGIN_ROUTE = '/login';


    // ─────────────────────────────────────────
    // PRIVATE: get token from localStorage
    // ─────────────────────────────────────────
    function _getToken() {
        return localStorage.getItem(TOKEN_KEY);
    }


    // ─────────────────────────────────────────
    // PRIVATE: build headers
    // Always sends Content-Type + Auth if token exists
    // ─────────────────────────────────────────
    function _buildHeaders(includeAuth = true) {
        const headers = {
            'Content-Type': 'application/json',
        };

        if (includeAuth) {
            const token = _getToken();
            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
            }
        }

        return headers;
    }


    // ─────────────────────────────────────────
    // PRIVATE: handle 401 — clear session + redirect
    // ─────────────────────────────────────────
    function _handleUnauthorized() {
        ['token', 'user_id', 'user_name'].forEach(k => localStorage.removeItem(k));
        window.location.href = LOGIN_ROUTE;
    }


    // ─────────────────────────────────────────
    // PRIVATE: core request handler
    // ─────────────────────────────────────────
    async function _request(method, endpoint, body = null, includeAuth = true) {
        const url = `${BASE_URL}${endpoint}`;

        const options = {
            method: method,
            headers: _buildHeaders(includeAuth),
        };

        if (body && method !== 'GET') {
            options.body = JSON.stringify(body);
        }

        try {
            const response = await fetch(url, options);

            // ── 401: token expired or missing (ignore for login endpoint) ──
            if (response.status === 401 && !endpoint.includes('/api/auth/login')) {
                _handleUnauthorized();
                return { success: false, message: 'Session expired. Please login again.' };
            }

            // ── Parse JSON ──
            let data;
            const contentType = response.headers.get('Content-Type') || '';

            if (contentType.includes('application/json')) {
                data = await response.json();
            } else {
                // Non-JSON response (shouldn't happen but handle gracefully)
                const text = await response.text();
                data = { success: false, message: text || 'Unexpected server response.' };
            }

            // ── Non-2xx but not 401 (e.g. 400, 404, 500) ──
            if (!response.ok && data.success === undefined) {
                data.success = false;
            }

            return data;

        } catch (err) {
            // ── Network failure (offline, server down) ──
            console.error(`[API] ${method} ${endpoint} failed:`, err);
            return {
                success: false,
                message: 'Network error. Please check your connection and try again.',
            };
        }
    }


    // ─────────────────────────────────────────
    // PUBLIC: GET
    // ─────────────────────────────────────────
    async function get(endpoint, includeAuth = true) {
        return _request('GET', endpoint, null, includeAuth);
    }


    // ─────────────────────────────────────────
    // PUBLIC: POST
    // ─────────────────────────────────────────
    async function post(endpoint, body = {}, includeAuth = true) {
        return _request('POST', endpoint, body, includeAuth);
    }


    // ─────────────────────────────────────────
    // PUBLIC: DELETE
    // ─────────────────────────────────────────
    async function del(endpoint, includeAuth = true) {
        return _request('DELETE', endpoint, null, includeAuth);
    }


    // ─────────────────────────────────────────
    // PUBLIC: getToken()
    // Expose token getter for other modules if needed
    // ─────────────────────────────────────────
    function getToken() {
        return _getToken();
    }


    // ─────────────────────────────────────────
    // EXPOSE
    // ─────────────────────────────────────────
    return {
        get,
        post,
        delete: del,
        getToken,
    };

})();