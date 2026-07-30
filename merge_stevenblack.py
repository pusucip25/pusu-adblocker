#!/usr/bin/env python3
"""Pusu AdBlocker + StevenBlack/hosts — merge optimizat."""
import json, re, urllib.request, time
from pathlib import Path

BASE = Path(r"C:/Users/Pusu/Projects/pusu-adblocker")
RULES_DIR = BASE / "rules"
MANIFEST = BASE / "manifest.json"
SB_URL = "https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts"

HIGH_PRI = {
    "doubleclick.net","googleadservices.com","googlesyndication.com",
    "google-analytics.com","googletagmanager.com","pagead2.googlesyndication.com",
    "adnxs.com","adsafeprotected.com","amazon-adsystem.com",
    "criteo.com","criteo.net","openx.net","outbrain.com","pubmatic.com",
    "rubiconproject.com","scorecardresearch.com","sharethis.com","taboola.com",
    "yieldmo.com","zedo.com","adsrvr.org","bluekai.com","casalemedia.com",
    "demdex.net","krxd.net","lijit.com","mathtag.com","media.net",
    "quantserve.com","rlcdn.com","smartadserver.com",
    "bat.bing.com","clarity.ms","hotjar.com","mouseflow.com","fullstory.com",
    "crazyegg.com","mixpanel.com","amplitude.com","segment.io","segment.com",
    "analytics.tiktok.com","moatads.com","exelator.com","simpli.fi",
    "serving-sys.com","adzerk.net","addthis.com","adsymptotic.com",
}

NO_BLOCK = {
    "google.com","googleapis.com","gstatic.com","youtube.com",
    "googlevideo.com","ytimg.com","microsoft.com","live.com","office.com",
    "github.com","githubusercontent.com","stackoverflow.com",
    "wikipedia.org","wikimedia.org","reddit.com","redd.it",
    "cdn.jsdelivr.net","unpkg.com","cloudflare.com","cloudfront.net",
    "amazon.com","facebook.com","fbcdn.net","instagram.com",
    "whatsapp.com","whatsapp.net","netflix.com","nflxvideo.net",
    "spotify.com","scdn.co","discord.com","discordapp.com",
    "notion.so","twimg.com",
}

ALL_RT = ["script","image","stylesheet","object","xmlhttprequest",
          "sub_frame","ping","font","media","websocket","webtransport",
          "webbundle","other"]

def suffixes(domain):
    parts = domain.split('.')
    for i in range(len(parts)-1):
        yield '.'.join(parts[i:])

def download_sb():
    print("   Downloading StevenBlack...")
    req = urllib.request.Request(SB_URL, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read().decode('utf-8', errors='ignore')
    domains = set()
    for line in data.split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        parts = line.split()
        if len(parts) >= 2 and parts[0] in ('0.0.0.0','127.0.0.1'):
            d = parts[1].strip().lower()
            if d and '.' in d and ':' not in d:
                domains.add(d)
    print(f"   -> {len(domains)} domains")
    return domains

def load_existing():
    covered = set()
    total = 0
    for f in sorted(RULES_DIR.glob('*.json')):
        try:
            rules = json.loads(f.read_text(encoding='utf-8'))
        except:
            continue
        fc = len(rules)
        total += fc
        print(f"   {f.name}: {fc} rules")
        for rule in rules:
            try:
                uf = rule.get("condition",{}).get("urlFilter","")
                clean = uf.replace('*://','').replace('*.','').replace('*','')
                clean = clean.rstrip('/').rstrip('^')
                dp = clean.split('/')[0]
                if dp and '.' in dp:
                    covered.add(dp.lower())
            except:
                continue
    print(f"   Total: {total} rules, {len(covered)} unique domains")
    return covered, total

def filter_new(sb_domains, covered):
    ip_re = re.compile(r'^\d+\.\d+\.\d+\.\d+$')
    
    # Build super-set with all suffixes for O(1) lookup
    cov_all = set(covered)
    for c in covered:
        for s in suffixes(c):
            cov_all.add(s)
    
    wl_all = set(NO_BLOCK)
    for w in NO_BLOCK:
        for s in suffixes(w):
            wl_all.add(s)
    
    hp_all = set(HIGH_PRI)
    for h in HIGH_PRI:
        for s in suffixes(h):
            hp_all.add(s)
    
    new = []
    t0 = time.time()
    
    for d in sb_domains:
        d = d.lower().strip()
        
        if d in cov_all or any(s in cov_all for s in suffixes(d)):
            continue
        if d in wl_all or any(s in wl_all for s in suffixes(d)):
            continue
        if ip_re.match(d):
            continue
        
        is_high = d in hp_all or any(s in hp_all for s in suffixes(d))
        new.append((d, is_high))
    
    elapsed = time.time() - t0
    new.sort(key=lambda x: (not x[1], x[0]))
    print(f"   Filtered {len(sb_domains)} domains in {elapsed:.1f}s")
    print(f"   -> {len(new)} new domains")
    return [d for d,_ in new]

def gen_rules(domains, start_id):
    rules = []
    rid = start_id
    for d in domains:
        rules.append({
            "id":rid,"priority":1,"action":{"type":"block"},
            "condition":{"urlFilter":f"*://{d}/*","resourceTypes":ALL_RT}
        })
        rid += 1
        rules.append({
            "id":rid,"priority":1,"action":{"type":"block"},
            "condition":{"urlFilter":f"*://*.{d}/*","resourceTypes":ALL_RT}
        })
        rid += 1
    return rules

def main():
    print("="*60)
    print("Pusu AdBlocker + StevenBlack/hosts")
    print("="*60)
    
    print("\n[1/4] Loading existing rules...")
    covered, total_rules = load_existing()
    
    print("\n[2/4] Downloading StevenBlack...")
    sb = download_sb()
    
    print("\n[3/4] Filtering new domains...")
    new = filter_new(sb, covered)
    
    CHROME_MAX = 30000
    BUFFER = 200
    slots = CHROME_MAX - total_rules - BUFFER
    max_domains = min(slots // 2, len(new))
    
    print(f"\n[4/4] Budget: {slots} available slots")
    print(f"   Max {max_domains} new domains ({max_domains*2} rules)")
    
    to_add = new[:max_domains]
    if not to_add:
        print("   No room for new rules!")
        return
    
    print(f"   Adding {len(to_add)} domains ({len(to_add)*2} rules)...")
    rules = gen_rules(to_add, 50001)
    
    out = RULES_DIR / "sbhosts.json"
    out.write_text(json.dumps(rules, indent=2) + '\n', encoding='utf-8')
    
    new_total = total_rules + len(rules)
    print(f"   Saved {len(rules)} rules -> sbhosts.json")
    print(f"   NEW TOTAL: {new_total}/{CHROME_MAX} rules")
    
    # Update manifest
    m = json.loads(MANIFEST.read_text(encoding='utf-8'))
    rr = m["declarative_net_request"]["rule_resources"]
    if not any(r["id"]=="rules_sbhosts" for r in rr):
        rr.append({"id":"rules_sbhosts","enabled":True,"path":"rules/sbhosts.json"})
    m["declarative_net_request"]["rule_resources"] = rr
    m["version"] = "1.6.0"
    m["description"] = "Ad blocker. v1.6: +StevenBlack hosts DNR rules"
    MANIFEST.write_text(json.dumps(m, indent=2) + '\n', encoding='utf-8')
    
    print(f"\n{'='*60}")
    print(f"DONE! 1.5.0 -> 1.6.0")
    print(f"{'='*60}")
    print(f"Sample new domains:")
    for d in to_add[:15]:
        print(f"   - {d}")
    if len(to_add) > 15:
        print(f"   ... +{len(to_add)-15} more")

if __name__ == "__main__":
    main()
