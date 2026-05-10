/**
 * voice.js
 * Standalone Voice Assistant — Browser-native STT + TTS.
 *
 * Flow:
 *   Page Load → Preload Voices → Auth Check → Start Session → Ready
 *   Tap Mic   → STT Listens → Send to /api/chatbot/message → Speak Reply
 *
 * Depends on: api.js, translation.js, auth.js, Chatbot (chatbot.js)
 */

(function () {

    // ─────────────────────────────────────────
    // STATE
    // ─────────────────────────────────────────
    let _recognition = null;      // SpeechRecognition instance
    let _isSpeaking = false;      // TTS is currently playing
    let _isListening = false;     // STT is active
    let _voices = [];             // Preloaded voice list (fixes async getVoices bug)

    // DOM refs
    const micBtn       = document.getElementById('mic-btn');
    const micIcon      = micBtn ? micBtn.querySelector('i') : null;
    const statusEl     = document.getElementById('voice-status');
    const transcriptEl = document.getElementById('transcript-text');
    const messagesEl   = document.getElementById('voice-messages');


    // ─────────────────────────────────────────
    // VOICES: Preload on page start
    // Fixes the browser bug where getVoices() returns [] on first call.
    // We listen for 'voiceschanged' and cache the full list immediately.
    // ─────────────────────────────────────────
    function preloadVoices() {
        if (!window.speechSynthesis) return;

        // Try to get voices immediately (some browsers have them ready)
        _voices = window.speechSynthesis.getVoices();

        // For browsers that load voices asynchronously (Chrome, Edge)
        // listen for the event and refresh the cache when ready
        window.speechSynthesis.onvoiceschanged = () => {
            _voices = window.speechSynthesis.getVoices();
            console.log(`[Voice] ${_voices.length} voices loaded.`);
        };
    }

    // ─────────────────────────────────────────
    // VOICES: Pick the best voice for a language code
    // Priority: exact match (ar-SA) → language prefix match (ar) → null
    // ─────────────────────────────────────────
    function pickVoice(langCode) {
        if (!_voices.length) return null;

        // 1. Try exact match first
        let voice = _voices.find(v => v.lang === langCode);

        // 2. Try prefix match (e.g. 'ar' matches 'ar-SA', 'ar-EG', etc.)
        if (!voice) {
            const prefix = langCode.split('-')[0];
            voice = _voices.find(v => v.lang.startsWith(prefix));
        }

        return voice || null;
    }


    // ─────────────────────────────────────────
    // HELPERS: STATUS & UI
    // ─────────────────────────────────────────
    function setStatus(text) {
        if (statusEl) statusEl.textContent = text;
    }

    function setTranscript(text) {
        if (transcriptEl) transcriptEl.textContent = text;
    }

    function scrollToBottom() {
        if (messagesEl) messagesEl.scrollTop = messagesEl.scrollHeight;
    }

    function formatTime(dateStr) {
        const d = dateStr ? new Date(dateStr) : new Date();
        return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }


    // ─────────────────────────────────────────
    // HELPERS: MARKDOWN — simple parser
    // ─────────────────────────────────────────
    function renderMarkdown(text) {
        if (!text) return '';
        return text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/\n/g, '<br>');
    }


    // ─────────────────────────────────────────
    // RENDER: Add a message bubble to the chat
    // ─────────────────────────────────────────
    function addBubble(role, content, isEmergency = false, timestamp = null) {
        if (!messagesEl) return;

        const wrapper = document.createElement('div');
        wrapper.className = `msg-bubble ${role}${isEmergency ? ' emergency' : ''}`;

        const timeStr = formatTime(timestamp);
        const safeContent = renderMarkdown(content);

        if (role === 'assistant') {
            wrapper.innerHTML = `
                <div class="msg-avatar"><i class="fa-solid fa-user-doctor fa-xs"></i></div>
                <div class="msg-content">
                    <div class="msg-text">${safeContent}</div>
                    <div style="display:flex;align-items:center;gap:6px;">
                        <span class="msg-time">${timeStr}</span>
                        <button class="play-btn" title="Play message" data-text="${content.replace(/"/g, '&quot;')}">
                            <i class="fa-solid fa-volume-high"></i>
                        </button>
                    </div>
                </div>`;
        } else {
            wrapper.innerHTML = `
                <div class="msg-content">
                    <div class="msg-text">${safeContent}</div>
                    <span class="msg-time">${timeStr}</span>
                </div>`;
        }

        messagesEl.appendChild(wrapper);

        // Attach play button listener
        const playBtn = wrapper.querySelector('.play-btn');
        if (playBtn) {
            playBtn.addEventListener('click', () => speakText(content, playBtn));
        }

        scrollToBottom();
        return wrapper;
    }


    // ─────────────────────────────────────────
    // RENDER: Typing indicator
    // ─────────────────────────────────────────
    function showTyping() {
        const el = document.createElement('div');
        el.id = 'typing-indicator';
        el.className = 'msg-bubble assistant';
        el.innerHTML = `
            <div class="msg-avatar"><i class="fa-solid fa-user-doctor fa-xs"></i></div>
            <div class="typing-dots">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>`;
        messagesEl.appendChild(el);
        scrollToBottom();
    }

    function hideTyping() {
        const el = document.getElementById('typing-indicator');
        if (el) el.remove();
    }


    // ─────────────────────────────────────────
    // TTS: Speak text aloud
    // Uses preloaded _voices and detects language from content.
    // ─────────────────────────────────────────
    function speakText(text, playBtnEl = null) {
        if (!window.speechSynthesis || !text) return;

        // Stop anything currently playing
        if (_isSpeaking) {
            window.speechSynthesis.cancel();
        }

        // 1. Detect language from the CONTENT itself (not the app UI lang)
        //    Arabic Unicode range: \u0600-\u06FF
        const hasArabic = /[\u0600-\u06FF]/.test(text);
        const targetLang = hasArabic ? 'ar-SA' : 'en-US';

        // 2. Clean markdown for clean audio output
        const cleanText = text
            .replace(/\*\*(.*?)\*\*/g, '$1')
            .replace(/\*(.*?)\*/g, '$1')
            .replace(/#+\s/g, '')
            .replace(/\n/g, '. ');

        // 3. Build utterance with the correct language
        const utterance = new SpeechSynthesisUtterance(cleanText);
        utterance.lang = targetLang;
        utterance.rate = 0.95;
        utterance.pitch = 1;

        // 4. Pick best matching voice from our preloaded cache
        const voice = pickVoice(targetLang);
        if (voice) {
            utterance.voice = voice;
            console.log(`[Voice] Speaking in: ${voice.lang} — ${voice.name}`);
        } else {
            console.warn(`[Voice] No voice found for ${targetLang}, using browser default.`);
        }

        utterance.onstart = () => {
            _isSpeaking = true;
            if (playBtnEl) playBtnEl.querySelector('i').className = 'fa-solid fa-stop';
        };

        utterance.onend = () => {
            _isSpeaking = false;
            if (playBtnEl) playBtnEl.querySelector('i').className = 'fa-solid fa-volume-high';
        };

        utterance.onerror = (e) => {
            console.error('[Voice] TTS error:', e.error);
            _isSpeaking = false;
            if (playBtnEl) playBtnEl.querySelector('i').className = 'fa-solid fa-volume-high';
        };

        window.speechSynthesis.speak(utterance);
    }


    // ─────────────────────────────────────────
    // STT: Set up SpeechRecognition
    // ─────────────────────────────────────────
    function setupSpeechRecognition() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            setStatus('Voice not supported in this browser.');
            if (micBtn) micBtn.disabled = true;
            return;
        }

        _recognition = new SpeechRecognition();
        _recognition.continuous = false;
        _recognition.interimResults = true;

        // STT uses app language setting (user chooses what language to SPEAK in)
        const lang = getCurrentLang();
        _recognition.lang = lang === 'ar' ? 'ar-SA' : 'en-US';

        _recognition.onresult = (event) => {
            let interim = '';
            let final = '';

            for (let i = event.resultIndex; i < event.results.length; i++) {
                const t = event.results[i][0].transcript;
                if (event.results[i].isFinal) {
                    final += t;
                } else {
                    interim += t;
                }
            }

            setTranscript(interim || final);

            if (final) {
                setTranscript('');
                handleUserMessage(final.trim());
            }
        };

        _recognition.onstart = () => {
            _isListening = true;
            if (micBtn) micBtn.classList.add('listening');
            if (micIcon) micIcon.className = 'fa-solid fa-stop';
            setStatus(getCurrentLang() === 'ar' ? 'جارٍ الاستماع...' : 'Listening...');
        };

        _recognition.onend = () => {
            _isListening = false;
            if (micBtn) micBtn.classList.remove('listening');
            if (micIcon) micIcon.className = 'fa-solid fa-microphone';
            setTranscript('');
            setStatus(getCurrentLang() === 'ar' ? 'اضغط للتحدث' : 'Tap the mic to start');
        };

        _recognition.onerror = (event) => {
            console.error('[Voice] STT error:', event.error);
            _isListening = false;
            if (micBtn) micBtn.classList.remove('listening');
            if (micIcon) micIcon.className = 'fa-solid fa-microphone';
            setStatus(getCurrentLang() === 'ar' ? 'تعذّر الاستماع. حاول مرة أخرى.' : 'Could not hear. Try again.');
        };
    }


    // ─────────────────────────────────────────
    // CORE: Handle a spoken user message
    // ─────────────────────────────────────────
    async function handleUserMessage(text) {
        if (!text) return;

        addBubble('user', text);
        showTyping();
        setStatus(getCurrentLang() === 'ar' ? 'جارٍ التفكير...' : 'Thinking...');

        const result = await Chatbot.sendMessage(text);

        hideTyping();

        if (!result.success) {
            setStatus(getCurrentLang() === 'ar' ? 'حدث خطأ.' : 'An error occurred.');
            return;
        }

        addBubble('assistant', result.reply, result.isEmergency);
        speakText(result.reply);

        setStatus(getCurrentLang() === 'ar' ? 'اضغط للتحدث' : 'Tap the mic to start');
    }


    // ─────────────────────────────────────────
    // MIC BUTTON: Toggle listening on tap
    // ─────────────────────────────────────────
    function bindMicButton() {
        if (!micBtn || !_recognition) return;

        micBtn.addEventListener('click', () => {
            if (_isListening) {
                _recognition.stop();
            } else {
                // Refresh STT lang on each tap (user may have switched language)
                _recognition.lang = getCurrentLang() === 'ar' ? 'ar-SA' : 'en-US';
                _recognition.start();
            }
        });
    }


    // ─────────────────────────────────────────
    // INIT: Entry point on page load
    // ─────────────────────────────────────────
    async function init() {
        // Step 1: Preload voices immediately so they're ready before first TTS call
        preloadVoices();

        const session = Auth.requireAuth();
        if (!session) return;

        const { user_id, user_name } = session;
        const lang = getCurrentLang();

        Chatbot.on('error', (msg) => setStatus(msg));

        await Chatbot.init(user_id, lang, user_name);

        setupSpeechRecognition();
        bindMicButton();

        setStatus(lang === 'ar' ? 'اضغط للتحدث' : 'Tap the mic to start');
    }


    // ─────────────────────────────────────────
    // START
    // ─────────────────────────────────────────
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
