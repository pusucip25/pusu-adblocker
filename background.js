// Pusu AdBlocker — Background Service Worker v1.5
// Popup-ul poate adăuga domenii la blocklist dinamic

const RULESET_IDS = ['rules_ads', 'rules_trackers', 'rules_annoyances', 'rules_custom'];

// --- Dynamic rule management ---
async function blockDomain(domain) {
    // Clean domain
    domain = domain.replace(/^www\./, '').toLowerCase();
    
    // Check if already blocked
    const existing = await chrome.declarativeNetRequest.getDynamicRules();
    const alreadyBlocked = existing.some(r => 
        r.condition.urlFilter.includes(domain)
    );
    if (alreadyBlocked) return { blocked: false, reason: 'Deja blocat' };
    
    // Get next ID
    const maxId = existing.reduce((max, r) => Math.max(max, r.id), 0);
    const newId = Math.max(maxId + 1, 60001);
    
    // Add rules for bare domain and wildcard
    const rules = [
        {
            id: newId,
            priority: 1,
            action: { type: 'block' },
            condition: {
                urlFilter: `*://${domain}/*`,
                resourceTypes: ['script','image','xmlhttprequest','sub_frame','ping','main_frame','websocket','other']
            }
        },
        {
            id: newId + 1,
            priority: 1,
            action: { type: 'block' },
            condition: {
                urlFilter: `*://*.${domain}/*`,
                resourceTypes: ['script','image','xmlhttprequest','sub_frame','ping','main_frame','websocket','other']
            }
        }
    ];
    
    await chrome.declarativeNetRequest.updateDynamicRules({
        addRules: rules
    });
    
    // Save to storage for persistence
    const stored = await chrome.storage.local.get('dynamicBlocked');
    const blocked = stored.dynamicBlocked || [];
    if (!blocked.includes(domain)) {
        blocked.push(domain);
        await chrome.storage.local.set({ dynamicBlocked: blocked });
    }
    
    return { blocked: true, domain };
}

async function getBlockedDomains() {
    const stored = await chrome.storage.local.get('dynamicBlocked');
    return stored.dynamicBlocked || [];
}

// --- Inițializare ---
async function init() {
    const stored = await chrome.storage.local.get(['enabled', 'totalBlocked']);
    const enabled = stored.enabled !== undefined ? stored.enabled : true;
    
    if (!stored.totalBlocked) {
        await chrome.storage.local.set({ totalBlocked: 0 });
    }
    
    if (enabled) {
        await chrome.declarativeNetRequest.updateEnabledRulesets({
            enableRulesetIds: RULESET_IDS
        }).catch(() => {});
    }
    
    // Restore dynamic rules from storage
    const dynamicBlocked = await getBlockedDomains();
    if (dynamicBlocked.length > 0) {
        const rules = [];
        let id = 60001;
        for (const domain of dynamicBlocked) {
            rules.push({
                id: id++, priority: 1, action: { type: 'block' },
                condition: { urlFilter: `*://${domain}/*`, resourceTypes: ['script','image','xmlhttprequest','sub_frame','ping','main_frame','websocket','other'] }
            });
            rules.push({
                id: id++, priority: 1, action: { type: 'block' },
                condition: { urlFilter: `*://*.${domain}/*`, resourceTypes: ['script','image','xmlhttprequest','sub_frame','ping','main_frame','websocket','other'] }
            });
        }
        await chrome.declarativeNetRequest.updateDynamicRules({ addRules: rules }).catch(() => {});
    }
    
    console.log(`🛡️ Pusu AdBlocker v1.5 — ${dynamicBlocked.length} domenii blocate dinamic`);
}

// --- Message handler ---
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
    if (msg.type === 'getStats') {
        chrome.storage.local.get(['totalBlocked', 'enabled']).then(stored => {
            getBlockedDomains().then(blocked => {
                sendResponse({ 
                    totalBlocked: stored.totalBlocked || 0, 
                    enabled: stored.enabled !== undefined ? stored.enabled : true,
                    dynamicBlocked: blocked.length
                });
            });
        });
        return true;
    }
    
    if (msg.type === 'setEnabled') {
        const enabled = msg.enabled;
        chrome.storage.local.set({ enabled });
        if (enabled) {
            chrome.declarativeNetRequest.updateEnabledRulesets({ enableRulesetIds: RULESET_IDS }).catch(() => {});
        } else {
            chrome.declarativeNetRequest.updateEnabledRulesets({ disableRulesetIds: RULESET_IDS }).catch(() => {});
        }
        sendResponse({ success: true });
        return false;
    }
    
    if (msg.type === 'blockDomain') {
        blockDomain(msg.domain).then(result => sendResponse(result));
        return true;
    }
    
    if (msg.type === 'getBlockedDomains') {
        getBlockedDomains().then(domains => sendResponse(domains));
        return true;
    }
});

// --- La install ---
chrome.runtime.onInstalled.addListener(async (details) => {
    if (details.reason === 'install' || details.reason === 'update') {
        await chrome.storage.local.set({ totalBlocked: 0, enabled: true });
        console.log('🛡️ Pusu AdBlocker instalat/actualizat.');
    }
});

init();
