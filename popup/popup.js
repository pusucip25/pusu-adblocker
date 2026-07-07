// Pusu AdBlocker — Popup Script v1.5
// Cu buton "Blochează site-ul asta"

let currentDomain = '';
let currentTabId = null;

// --- Load stats ---
async function loadStats() {
  try {
    const response = await chrome.runtime.sendMessage({ type: 'getStats' });
    const totalBlocked = response.totalBlocked || 0;
    const enabled = response.enabled !== undefined ? response.enabled : true;
    const dynamicBlocked = response.dynamicBlocked || 0;
    
    document.getElementById('blockedTotal').textContent = formatNumber(totalBlocked);
    document.getElementById('blockedDynamic').textContent = String(dynamicBlocked);
    
    // Update toggle
    const toggle = document.getElementById('toggleBtn');
    const statusDot = document.getElementById('statusDot');
    const statusText = document.getElementById('statusText');
    
    toggle.checked = enabled;
    if (enabled) {
      statusDot.classList.remove('off');
      statusText.textContent = 'Activ';
    } else {
      statusDot.classList.add('off');
      statusText.textContent = 'Oprit';
    }
    
    // Get current tab
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tab && tab.url) {
      currentTabId = tab.id;
      try {
        const url = new URL(tab.url);
        currentDomain = url.hostname.replace(/^www\./, '');
        document.getElementById('currentDomain').textContent = currentDomain;
      } catch {
        currentDomain = '';
        document.getElementById('currentDomain').textContent = tab.url.substring(0, 40);
      }
    }
    
    // Check if current domain is already blocked
    await updateBlockButton();
    
  } catch (e) {
    console.error('Popup error:', e);
  }
}

async function updateBlockButton() {
  const btn = document.getElementById('blockBtn');
  if (!currentDomain) {
    btn.textContent = '🚫 Blochează site-ul asta';
    btn.classList.add('blocked');
    return;
  }
  
  // Check if already blocked (dynamic)
  const blockedDomains = await chrome.runtime.sendMessage({ type: 'getBlockedDomains' });
  if (blockedDomains.includes(currentDomain)) {
    btn.textContent = '✅ Deja blocat';
    btn.classList.add('blocked');
  } else {
    btn.textContent = '🚫 Blochează ' + currentDomain;
    btn.classList.remove('blocked');
  }
}

// --- Block domain ---
async function blockCurrentSite() {
  if (!currentDomain) return;
  
  const btn = document.getElementById('blockBtn');
  btn.textContent = '⏳ Se blochează...';
  
  const result = await chrome.runtime.sendMessage({
    type: 'blockDomain',
    domain: currentDomain
  });
  
  showToast(result.blocked 
    ? `✅ ${currentDomain} blocat!` 
    : `ℹ️ ${result.reason || 'Eroare'}`);
  
  await updateBlockButton();
  loadStats();
}

// --- Toggle on/off ---
async function toggleAdblocker(enabled) {
  await chrome.runtime.sendMessage({ type: 'setEnabled', enabled });
  loadStats();
}

function showToast(msg) {
  const toast = document.getElementById('toast');
  toast.textContent = msg;
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), 2000);
}

function formatNumber(n) {
  if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M';
  if (n >= 1000) return (n / 1000).toFixed(1) + 'K';
  return String(n);
}

// --- Init ---
document.addEventListener('DOMContentLoaded', () => {
  loadStats();
  
  document.getElementById('blockBtn').addEventListener('click', blockCurrentSite);
  
  document.getElementById('toggleBtn').addEventListener('change', (e) => {
    toggleAdblocker(e.target.checked);
  });
});

chrome.runtime.onMessage.addListener((msg) => {
  if (msg.type === 'statsUpdated') loadStats();
});
