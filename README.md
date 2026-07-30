# 🛡️ Pusu AdBlocker

**Ad blocker făcut manual — zero tracking, 100% local, open source.**

Creat de [Pusu](https://github.com/pusu) împreună cu Hermes Agent, după o noapte întreagă de încercări, bug-uri reparate pe loc și blesteme la adresa scripturilor de popup. 🍻

---

## 📖 Povestea

Totul a început când un site de filme (fsonline.app) deschidea **10 pagini de reclame** la un singur click. Am zis: hai să facem un ad blocker. Nu unul oarecare — unul făcut de noi, fără niciun third-party, fără tracking, fără "popular extensions" care-ți vând datele.

După ore de:
- ❌ "Failed to load extension: non-ASCII characters"  
- ❌ "ID-uri duplicate între fișiere"  
- ❌ Reguli care blocau doar `*.domain.com` dar nu și `domain.com` gol  
- ❌ Content script-uri care nu prindeau toate metodele de popup  
- ❌ Tab closing prea agresiv (bloca și navigarea normală)  
- ✅ Și multe iterații mai târziu...

...am ajuns la **v1.5** — un ad blocker care folosește **28.000+ reguli** din EasyList, EasyPrivacy și Fanboy Annoyances, plus un sistem dinamic prin care poți adăuga domenii noi direct din popup.

---

## 🚀 Features

| Feature | Detalii |
|---|---|
| **28.368 reguli statice** | EasyList (12.043) + EasyPrivacy (12.000) + Fanboy Annoyances (3.930) + custom (395) |
| **Reguli dinamice** | Poți bloca orice domeniu nou direct din popup, fără să modifici codul |
| **Zero tracking** | Nu trimite date nicăieri. Nu colectează nimic. Codul e 100% local. |
| **Content script anti-popup** | Blochează `window.open` + `HTMLAnchorElement.click()` + event listeners |
| **Toggle on/off** | Oprești/pornești dintr-un click din popup |
| **Statistici** | Vezi câte reclame ai blocat în total și pe pagina curentă |
| **Dark theme** | Interfață curată, dark, făcută să arate bine |

---

## 📦 Instalare

1. **Clone** acest repo:
   ```bash
   git clone https://github.com/pusucip25/pusu-adblocker.git
   ```

2. Intră în **Chrome** → `chrome://extensions`

3. Activează **Developer mode** (toggle dreapta-sus)

4. Click **Load unpacked** → selectează folderul clonat

5. ✅ Gata! Iconița 🛡️ apare lângă bara de adrese.

---

## 🔄 Cum actualizezi regulile

Dacă vrei să descarci cele mai noi liste de filtre:

```bash
python generate_rules.py
```

Apoi dă **Refresh (🔄)** pe extensie în `chrome://extensions`.

---

## 🎯 Cum adaugi un domeniu nou

Când o reclamă nouă se strecoară:

1. Click pe iconița 🛡️ din bara Chrome
2. Apasă **🚫 Blochează site-ul asta**
3. Gata! Nu o să mai vezi reclama aia niciodată.

---

## 🏗️ Structură

```
pusu-adblocker/
├── manifest.json          # Manifest V3
├── background.js          # Service worker + reguli dinamice
├── content.js             # Content script anti-popup
├── generate_rules.py      # Script care descarcă și convertește EasyList
├── popup/
│   ├── popup.html         # Interfața popup
│   └── popup.js           # Logica popup-ului
├── rules/
│   ├── ads.json           # 12.043 reguli din EasyList
│   ├── trackers.json      # 12.000 reguli din EasyPrivacy
│   ├── annoyances.json    # 3.938 reguli din Fanboy Annoyances
│   └── custom.json        # 395+ domenii adăugate manual
└── icons/                 # Iconițe 16/48/128px
```

---

## 🛠️ Tech Stack

- **Manifest V3** — ultimul standard Chrome
- **declarativeNetRequest** — blocare la nivel de rețea, fără overhead
- **Vanilla JS** — fără framework-uri, fără dependențe
- **Python** — doar pentru scriptul de generare a regulilor

---

## 🤝 Contribuie

Ai găsit un domeniu de reclame care nu e blocat? Deschide un issue sau fă un PR cu domeniul în `rules/custom.json`.

Sau dă-i un ⭐ dacă ți-e util!

---

## 📜 Licență

MIT — fă ce vrei cu el, doar dă credit.

---

**Făcut cu ❤️ (și multă cafea) de Pusu & Hermes Agent, 2026**
