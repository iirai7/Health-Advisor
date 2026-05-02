/**
 * translation.js
 * Client-side i18n helper for AR/EN switching.
 *
 * Usage in HTML:
 *   <span data-i18n="nav.home">Home</span>
 *   <input data-i18n-placeholder="auth.email_placeholder" />
 *   <input data-i18n-aria="common.close" />
 *
 * Called automatically on page load and on language toggle.
 * Exposes: applyTranslations(lang), t(key, lang), getCurrentLang()
 */

(function () {
    // ─────────────────────────────────────────
    // STATE
    // ─────────────────────────────────────────
    let _translations = null;   // full JSON object once loaded
    let _currentLang = 'en';   // active language

    // ─────────────────────────────────────────
    // LOAD translations from JSON (once)
    // ─────────────────────────────────────────
    async function loadTranslations() {
        if (_translations) return _translations;

        try {
            const res = await fetch('/static/js/translation.json');
            if (!res.ok) throw new Error(`Failed to load translations: ${res.status}`);
            _translations = await res.json();
            return _translations;
        } catch (err) {
            console.error('[translation.js]', err);
            _translations = {};
            return _translations;
        }
    }

    // ─────────────────────────────────────────
    // RESOLVE a dot-notation key
    // e.g. "nav.home" → translations[lang]["nav"]["home"]
    // ─────────────────────────────────────────
    function resolve(obj, keyPath) {
        return keyPath.split('.').reduce((acc, part) => {
            return acc && acc[part] !== undefined ? acc[part] : null;
        }, obj);
    }

    // ─────────────────────────────────────────
    // PUBLIC: t(key, lang?)
    // Resolve a single translation key.
    // Falls back to EN, then to the key itself.
    // ─────────────────────────────────────────
    function t(key, lang) {
        if (!_translations) return key;
        const language = lang || _currentLang;
        const value = resolve(_translations[language], key)
            ?? resolve(_translations['en'], key)
            ?? key;
        return value;
    }

    // ─────────────────────────────────────────
    // PUBLIC: getCurrentLang()
    // ─────────────────────────────────────────
    function getCurrentLang() {
        return _currentLang;
    }

    // ─────────────────────────────────────────
    // APPLY all data-i18n attributes in the DOM
    // ─────────────────────────────────────────
    function applyDOM(lang) {
        if (!_translations) return;

        const dict = _translations[lang] || _translations['en'] || {};

        // data-i18n → textContent
        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            const value = resolve(dict, key) ?? resolve(_translations['en'], key) ?? key;
            if (value !== null) el.textContent = value;
        });

        // data-i18n-placeholder → placeholder attribute
        document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
            const key = el.getAttribute('data-i18n-placeholder');
            const value = resolve(dict, key) ?? resolve(_translations['en'], key) ?? key;
            if (value !== null) el.setAttribute('placeholder', value);
        });

        // data-i18n-aria → aria-label attribute
        document.querySelectorAll('[data-i18n-aria]').forEach(el => {
            const key = el.getAttribute('data-i18n-aria');
            const value = resolve(dict, key) ?? resolve(_translations['en'], key) ?? key;
            if (value !== null) el.setAttribute('aria-label', value);
        });

        // data-i18n-title → title attribute (tooltip)
        document.querySelectorAll('[data-i18n-title]').forEach(el => {
            const key = el.getAttribute('data-i18n-title');
            const value = resolve(dict, key) ?? resolve(_translations['en'], key) ?? key;
            if (value !== null) el.setAttribute('title', value);
        });

        // data-i18n-html → innerHTML (use sparingly, only for trusted content)
        document.querySelectorAll('[data-i18n-html]').forEach(el => {
            const key = el.getAttribute('data-i18n-html');
            const value = resolve(dict, key) ?? resolve(_translations['en'], key) ?? key;
            if (value !== null) el.innerHTML = value;
        });
    }

    // ─────────────────────────────────────────
    // PUBLIC: applyTranslations(lang)
    // Called by base.html on load + on toggle.
    // ─────────────────────────────────────────
    async function applyTranslations(lang) {
        _currentLang = lang || localStorage.getItem('lang') || 'en';

        await loadTranslations();
        applyDOM(_currentLang);

        // Dispatch event so individual pages can react if needed
        document.dispatchEvent(new CustomEvent('langChanged', { detail: { lang: _currentLang } }));
    }

    // ─────────────────────────────────────────
    // AUTO-INIT on DOM ready
    // ─────────────────────────────────────────
    function init() {
        const lang = localStorage.getItem('lang') || 'en';
        applyTranslations(lang);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // ─────────────────────────────────────────
    // EXPOSE globals (used by base.html + pages)
    // ─────────────────────────────────────────
    window.applyTranslations = applyTranslations;
    window.t = t;
    window.getCurrentLang = getCurrentLang;

})();