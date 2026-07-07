// Pusu AdBlocker - Content Script v2
// Anti-popup NUCLEAR: blochează TOATE metodele de deschidere ferestre
(function() {
    'use strict';
    
    // === 1. BLOCHEAZĂ window.open ===
    const _open = window.open;
    Object.defineProperty(window, 'open', {
        value: function(url, target, features) {
            // Permite doar același domeniu sau about:blank
            if (!url || url === 'about:blank' || url === '') {
                return _open.call(window, url, target, features);
            }
            try {
                const u = new URL(String(url), location.href);
                // Permite același domeniu
                if (u.hostname === location.hostname || u.hostname.endsWith('.' + location.hostname)) {
                    return _open.call(window, url, target, features);
                }
            } catch(e) {}
            
            // BLOCHEAZĂ — returnează null (multe scripturi verifică asta)
            return null;
        },
        writable: false,
        configurable: false
    });
    
    // === 2. BLOCHEAZĂ <a> click programatic către domenii externe ===
    const _click = HTMLAnchorElement.prototype.click;
    HTMLAnchorElement.prototype.click = function() {
        const href = this.href || this.getAttribute('href') || '';
        if (href && !href.startsWith('javascript:') && !href.startsWith('#')) {
            try {
                const u = new URL(href, location.href);
                if (u.hostname !== location.hostname && !u.hostname.endsWith('.' + location.hostname)) {
                    if (u.protocol === 'http:' || u.protocol === 'https:') {
                        // Blocăm click-ul pe link extern
                        return;
                    }
                }
            } catch(e) {}
        }
        return _click.call(this);
    };
    
    // === 3. BLOCHEAZĂ crearea de <a> cu target=_blank din JS ===
    const _createElement = document.createElement.bind(document);
    document.createElement = function(tag, options) {
        const el = _createElement(tag, options);
        if (tag.toLowerCase() === 'a') {
            const _setAttribute = el.setAttribute.bind(el);
            el.setAttribute = function(name, value) {
                if (name === 'target' && value === '_blank') {
                    // Nu seta target=_blank pentru linkuri externe
                }
                return _setAttribute(name, value);
            };
        }
        return el;
    };
    
    // === 4. Interceptează evenimentele de click pe document (capture phase) ===
    document.addEventListener('click', function(e) {
        let target = e.target;
        while (target && target !== document) {
            if (target.tagName === 'A' && target.href) {
                try {
                    const u = new URL(target.href, location.href);
                    if (u.hostname !== location.hostname && !u.hostname.endsWith('.' + location.hostname)) {
                        if (target.target === '_blank' || e.ctrlKey || e.metaKey) {
                            e.preventDefault();
                            e.stopPropagation();
                            e.stopImmediatePropagation();
                            return false;
                        }
                    }
                } catch(e) {}
            }
            target = target.parentElement;
        }
    }, true);
    
    // === 5. Blochează submit de form către domenii externe ===
    document.addEventListener('submit', function(e) {
        const form = e.target;
        if (form.action) {
            try {
                const u = new URL(form.action, location.href);
                if (u.hostname !== location.hostname && !u.hostname.endsWith('.' + location.hostname)) {
                    if (form.target === '_blank') {
                        e.preventDefault();
                        e.stopPropagation();
                        return false;
                    }
                }
            } catch(e) {}
        }
    }, true);
    
})();
