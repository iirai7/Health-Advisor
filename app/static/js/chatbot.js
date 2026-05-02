/**
 * chatbot.js
 * Handles chatbot session management, messaging, and emergency flag.
 *
 * Depends on: api.js, translation.js, auth.js
 * Exposes: global `Chatbot` object
 *
 * Usage in chatbot.html {% block scripts %}:
 *   await Chatbot.init(userId, language, memberName);
 *   await Chatbot.sendMessage(text);
 *   Chatbot.reset();
 */

const Chatbot = (function () {

    // ─────────────────────────────────────────
    // STATE
    // ─────────────────────────────────────────
    let _userId = null;
    let _sessionId = null;
    let _language = 'en';
    let _memberName = '';
    let _isLoading = false;

    // Callbacks set by the page
    let _onMessage = null;   // fn({ role, content, isEmergency })
    let _onLoading = null;   // fn(bool)
    let _onEmergency = null;   // fn(message)
    let _onError = null;   // fn(message)


    // ─────────────────────────────────────────
    // PRIVATE: set loading state
    // ─────────────────────────────────────────
    function _setLoading(state) {
        _isLoading = state;
        if (typeof _onLoading === 'function') _onLoading(state);
    }


    // ─────────────────────────────────────────
    // PRIVATE: trigger emergency
    // ─────────────────────────────────────────
    function _triggerEmergency(replyText) {
        const msg = t('chatbot.emergency_msg');
        // Show global banner from base.html
        if (typeof showEmergency === 'function') showEmergency(msg);
        // Also call page-level handler if set
        if (typeof _onEmergency === 'function') _onEmergency(msg);
    }


    // ─────────────────────────────────────────
    // PUBLIC: on(event, callback)
    // Register page-level event handlers.
    // Events: 'message', 'loading', 'emergency', 'error'
    // ─────────────────────────────────────────
    function on(event, callback) {
        if (event === 'message') _onMessage = callback;
        if (event === 'loading') _onLoading = callback;
        if (event === 'emergency') _onEmergency = callback;
        if (event === 'error') _onError = callback;
    }


    // ─────────────────────────────────────────
    // PUBLIC: init(userId, language, memberName)
    // Start or resume a session.
    // Calls /api/chatbot/start and stores session_id.
    // Returns { success, sessionId } or { success: false }
    // ─────────────────────────────────────────
    async function init(userId, language, memberName) {
        _userId = userId;
        _language = language || getCurrentLang() || 'en';
        _memberName = memberName || '';

        _setLoading(true);

        const result = await API.post('/api/chatbot/start', {
            user_id: _userId,
            language: _language,
        });

        _setLoading(false);

        if (!result.success) {
            console.error('[Chatbot.init]', result.message);
            if (typeof _onError === 'function') _onError(result.message || t('common.error'));
            return { success: false };
        }

        _sessionId = result.session_id;

        // Emit the first question from the backend (opening prompt for current stage)
        const firstQ = result.first_question || result.message || '';
        if (firstQ && typeof _onMessage === 'function') {
            _onMessage({ role: 'assistant', content: firstQ, isEmergency: false });
        }

        return { success: true, sessionId: _sessionId };
    }


    // ─────────────────────────────────────────
    // PUBLIC: sendMessage(text)
    // Send a user message and receive assistant reply.
    // Emits via _onMessage callback.
    // Returns { success, reply, isEmergency } or { success: false }
    // ─────────────────────────────────────────
    async function sendMessage(text) {
        if (!_sessionId) {
            console.error('[Chatbot.sendMessage] No active session.');
            if (typeof _onError === 'function') _onError(t('common.error'));
            return { success: false };
        }

        if (_isLoading) return { success: false };

        const trimmed = text.trim();
        if (!trimmed) return { success: false };

        // Emit user message immediately (optimistic UI)
        if (typeof _onMessage === 'function') {
            _onMessage({ role: 'user', content: trimmed, isEmergency: false });
        }

        _setLoading(true);

        const result = await API.post('/api/chatbot/message', {
            user_id: _userId,
            session_id: _sessionId,
            message: trimmed,
        });

        _setLoading(false);

        if (!result.success) {
            console.error('[Chatbot.sendMessage]', result.message);
            if (typeof _onError === 'function') _onError(result.message || t('common.error'));
            return { success: false };
        }

        const reply = result.reply || '';
        const isEmergency = result.is_emergency === true;

        // Emit assistant reply
        if (typeof _onMessage === 'function') {
            _onMessage({ role: 'assistant', content: reply, isEmergency });
        }

        // Trigger emergency flow if flagged
        if (isEmergency) _triggerEmergency(reply);

        return { success: true, reply, isEmergency };
    }


    // ─────────────────────────────────────────
    // PUBLIC: reset(language?)
    // Archive current session and open a fresh one.
    // Returns { success, sessionId } or { success: false }
    // ─────────────────────────────────────────
    async function reset(language) {
        if (!_sessionId) return { success: false };

        _setLoading(true);

        const result = await API.post('/api/chatbot/reset', {
            user_id: _userId,
            session_id: _sessionId,
            language: language || _language,
        });

        _setLoading(false);

        if (!result.success) {
            console.error('[Chatbot.reset]', result.message);
            if (typeof _onError === 'function') _onError(result.message || t('common.error'));
            return { success: false };
        }

        _sessionId = result.session_id;

        // Hide emergency banner if visible
        if (typeof hideEmergency === 'function') hideEmergency();

        return { success: true, sessionId: _sessionId };
    }


    // ─────────────────────────────────────────
    // PUBLIC: getHistory(userId)
    // Fetch all past sessions for a user.
    // Returns { success, sessions } or { success: false }
    // ─────────────────────────────────────────
    async function getHistory(userId) {
        const result = await API.get(`/api/chatbot/history/${userId || _userId}`);

        if (!result.success) {
            console.error('[Chatbot.getHistory]', result.message);
            return { success: false, sessions: [] };
        }

        return { success: true, sessions: result.history || [] };
    }


    // ─────────────────────────────────────────
    // PUBLIC: getState()
    // Returns current session state (useful for debugging)
    // ─────────────────────────────────────────
    function getState() {
        return {
            userId: _userId,
            sessionId: _sessionId,
            language: _language,
            memberName: _memberName,
            isLoading: _isLoading,
        };
    }


    // ─────────────────────────────────────────
    // EXPOSE
    // ─────────────────────────────────────────
    return {
        on,
        init,
        sendMessage,
        reset,
        getHistory,
        getState,
    };

})();