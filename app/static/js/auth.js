/**
 * auth.js
 * Central authentication logic for Smart Diagnosis app.
 *
 * Exposes a global `Auth` object. No DOM manipulation here —
 * each page's own script handles forms and calls these methods.
 *
 * Usage:
 *   const result = await Auth.login(email, password);
 *   if (result.success) { ... } else { showError(result.message); }
 */

const Auth = (function () {

    // ─────────────────────────────────────────
    // CONSTANTS
    // ─────────────────────────────────────────
    const STORAGE_KEYS = {
        TOKEN: 'token',
        USER_ID: 'user_id',
        USER_NAME: 'user_name',
    };

    const ROUTES = {
        DASHBOARD: '/dashboard',
        LOGIN: '/login',
        VERIFY_OTP: '/verify-otp',
        RESET_PASSWORD: '/reset-password',
    };


    // ─────────────────────────────────────────
    // PRIVATE: save session to localStorage
    // ─────────────────────────────────────────
    function _saveSession({ token, user_id, user_name }) {
        localStorage.setItem(STORAGE_KEYS.TOKEN, token);
        localStorage.setItem(STORAGE_KEYS.USER_ID, String(user_id));
        localStorage.setItem(STORAGE_KEYS.USER_NAME, user_name);
    }


    // ─────────────────────────────────────────
    // PRIVATE: clear session from localStorage
    // ─────────────────────────────────────────
    function _clearSession() {
        Object.values(STORAGE_KEYS).forEach(key => localStorage.removeItem(key));
    }


    // ─────────────────────────────────────────
    // PRIVATE: redirect helper
    // ─────────────────────────────────────────
    function _redirect(path) {
        window.location.href = path;
    }


    // ─────────────────────────────────────────
    // PUBLIC: getSession()
    // Returns current session data from localStorage.
    // Returns null if no token found.
    // ─────────────────────────────────────────
    function getSession() {
        const token = localStorage.getItem(STORAGE_KEYS.TOKEN);
        if (!token) return null;
        return {
            token: token,
            user_id: parseInt(localStorage.getItem(STORAGE_KEYS.USER_ID)),
            user_name: localStorage.getItem(STORAGE_KEYS.USER_NAME),
        };
    }


    // ─────────────────────────────────────────
    // PUBLIC: isLoggedIn()
    // ─────────────────────────────────────────
    function isLoggedIn() {
        return !!localStorage.getItem(STORAGE_KEYS.TOKEN);
    }


    // ─────────────────────────────────────────
    // PUBLIC: register(name, email, password, phone)
    // Registers new user. On success redirects to /verify-otp.
    // Returns { success, message }
    // ─────────────────────────────────────────
    async function register(name, email, password, phone_number) {
        try {
            const res = await API.post('/api/auth/register', {
                name,
                email,
                password,
                phone_number: phone_number || undefined,
            });

            if (res.success) {
                // Redirect to OTP page — pass email as query param
                _redirect(`${ROUTES.VERIFY_OTP}?email=${encodeURIComponent(email)}`);
            }

            return res;

        } catch (err) {
            console.error('[Auth.register]', err);
            return { success: false, message: t('common.error') };
        }
    }


    // ─────────────────────────────────────────
    // PUBLIC: verifyOtp(email, otp)
    // Verifies OTP after registration.
    // On success saves session and redirects to /dashboard.
    // Returns { success, message }
    // ─────────────────────────────────────────
    async function verifyOtp(email, otp) {
        try {
            const res = await API.post('/api/auth/verify-otp', { email, otp });

            if (res.success) {
                _saveSession({
                    token: res.token,
                    user_id: res.user_id,
                    user_name: res.user_name,
                });
                _redirect(ROUTES.DASHBOARD);
            }

            return res;

        } catch (err) {
            console.error('[Auth.verifyOtp]', err);
            return { success: false, message: t('common.error') };
        }
    }


    // ─────────────────────────────────────────
    // PUBLIC: resendOtp(email)
    // Resends OTP to user's email.
    // Returns { success, message }
    // ─────────────────────────────────────────
    async function resendOtp(email) {
        try {
            const res = await API.post('/api/auth/resend-otp', { email });
            return res;
        } catch (err) {
            console.error('[Auth.resendOtp]', err);
            return { success: false, message: t('common.error') };
        }
    }


    // ─────────────────────────────────────────
    // PUBLIC: login(email, password)
    // On success saves session and redirects to /dashboard.
    // Returns { success, message }
    // ─────────────────────────────────────────
    async function login(email, password) {
        try {
            const res = await API.post('/api/auth/login', { email, password });

            if (res.success) {
                _saveSession({
                    token: res.token,
                    user_id: res.user_id,
                    user_name: res.user_name,
                });
                _redirect(ROUTES.DASHBOARD);
            }

            return res;

        } catch (err) {
            console.error('[Auth.login]', err);
            return { success: false, message: t('common.error') };
        }
    }


    // ─────────────────────────────────────────
    // PUBLIC: forgotPassword(email)
    // Sends reset OTP to email.
    // On success redirects to /reset-password.
    // Returns { success, message }
    // ─────────────────────────────────────────
    async function forgotPassword(email) {
        try {
            const res = await API.post('/api/auth/forgot-password', { email });

            if (res.success) {
                _redirect(`${ROUTES.RESET_PASSWORD}?email=${encodeURIComponent(email)}`);
            }

            return res;

        } catch (err) {
            console.error('[Auth.forgotPassword]', err);
            return { success: false, message: t('common.error') };
        }
    }


    // ─────────────────────────────────────────
    // PUBLIC: resetPassword(email, otp, newPassword)
    // Resets password using OTP.
    // On success redirects to /login.
    // Returns { success, message }
    // ─────────────────────────────────────────
    async function resetPassword(email, otp, new_password) {
        try {
            const res = await API.post('/api/auth/reset-password', {
                email,
                otp,
                new_password,
            });

            if (res.success) {
                _redirect(ROUTES.LOGIN);
            }

            return res;

        } catch (err) {
            console.error('[Auth.resetPassword]', err);
            return { success: false, message: t('common.error') };
        }
    }


    // ─────────────────────────────────────────
    // PUBLIC: logout()
    // Clears session and redirects to /login.
    // ─────────────────────────────────────────
    function logout() {
        _clearSession();
        _redirect(ROUTES.LOGIN);
    }


    // ─────────────────────────────────────────
    // PUBLIC: requireAuth()
    // Call at top of any protected page script.
    // Redirects to /login if no session found.
    // Returns session or null.
    // ─────────────────────────────────────────
    function requireAuth() {
        const session = getSession();
        if (!session) {
            _redirect(ROUTES.LOGIN);
            return null;
        }
        return session;
    }


    // ─────────────────────────────────────────
    // EXPOSE
    // ─────────────────────────────────────────
    return {
        getSession,
        isLoggedIn,
        register,
        verifyOtp,
        resendOtp,
        login,
        forgotPassword,
        resetPassword,
        logout,
        requireAuth,
    };

})();