#!/usr/bin/env python3
"""
Convertește filtrele EasyList/EasyPrivacy în reguli declarativeNetRequest pentru Chrome MV3.
Rulează o singură dată pentru a genera fișierele rules/*.json
"""

import json
import re
import urllib.request
import os
from pathlib import Path

# Sursele de filtre (aceleași folosite de uBlock Origin)
SOURCES = {
    "ads": [
        "https://easylist.to/easylist/easylist.txt",
    ],
    "trackers": [
        "https://easylist.to/easylist/easyprivacy.txt",
    ],
    "annoyances": [
        "https://secure.fanboy.co.nz/fanboy-annoyance.txt",
    ],
}

# Tipurile de resurse pe care le blocăm
ALL_RESOURCES = [
    "script", "image", "stylesheet", "object", "xmlhttprequest",
    "sub_frame", "ping", "font", "media", "websocket", "webtransport",
    "webbundle", "other"
]

def url_filter_from_abp(rule):
    """
    Convertește o regulă ABP (AdBlock Plus) în urlFilter pentru DNR.
    Suportă || (domain anchor), | (start/end anchor), ^ (separator), * (wildcard)
    """
    # ||domain.com^ → domain.com
    # ||domain.com/path^ → domain.com/path
    
    filter_str = rule
    
    # Remove options ($script, $image, etc.)
    options_match = re.search(r'\$(.+)', filter_str)
    options = set()
    if options_match:
        options_str = options_match.group(1)
        options = set(o.strip() for o in options_str.split(','))
        filter_str = filter_str[:options_match.start()]
    
    # || at start = match any subdomain
    if filter_str.startswith('||'):
        filter_str = filter_str[2:]  # Remove ||
        # The || acts as a domain anchor, so we use it differently
        # For DNR: ||example.com^ → urlFilter: "*://*.example.com/*"
        
    # | at start = match at beginning of URL
    elif filter_str.startswith('|'):
        filter_str = filter_str[1:]
        
    # | at end = match at end of URL  
    if filter_str.endswith('|'):
        filter_str = filter_str[:-1]
        
    # Remove ^ (separator character in ABP)
    filter_str = filter_str.replace('^', '')
    
    # Clean up
    filter_str = filter_str.strip()
    
    # Remove protocol if present
    filter_str = re.sub(r'^https?://', '', filter_str)
    
    return filter_str, options


def get_resource_types(options):
    """Extrage resource types din opțiunile ABP"""
    type_map = {
        'script': 'script',
        'image': 'image', 
        'stylesheet': 'stylesheet',
        'object': 'object',
        'object-subrequest': 'object',
        'xmlhttprequest': 'xmlhttprequest',
        'xhr': 'xmlhttprequest',
        'subdocument': 'sub_frame',
        'sub_frame': 'sub_frame',
        'ping': 'ping',
        'font': 'font',
        'media': 'media',
        'websocket': 'websocket',
        'other': 'other',
        'document': None,  # Skip document rules (cosmetic)
        'elemhide': None,  # Skip element hiding
        'generichide': None,
        'genericblock': None,
    }
    
    types = set()
    for opt in options:
        if opt.startswith('domain=') or opt.startswith('~'):
            continue
        if opt == 'document' or opt == 'elemhide' or opt == 'generichide' or opt == 'genericblock':
            continue
        if opt in type_map and type_map[opt]:
            types.add(type_map[opt])
    
    return list(types) if types else None


def download_filter_list(url, max_rules=15000):
    """Descarcă o listă de filtre și o convertește în reguli DNR"""
    print(f"  Downloading: {url}")
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=30) as response:
            content = response.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"  ERROR downloading {url}: {e}")
        return []
    
    rules = []
    rule_id = 1
    block_count = 0
    
    for line in content.split('\n'):
        if rule_id > max_rules:
            break
            
        line = line.strip()
        
        # Skip comments, empty lines, element hiding, whitelist
        if not line or line.startswith('!') or line.startswith('['):
            continue
        if line.startswith('@@'):  # Whitelist
            continue
        if '##' in line or '#@#' in line:  # Element hiding
            continue
            
        # Skip if it doesn't look like a URL filter
        if not any(c in line for c in ['/', '.', '?', '=']):
            continue
            
        try:
            url_filter, options = url_filter_from_abp(line)
            if not url_filter or len(url_filter) < 3:
                continue
            
            # Chrome DNR urlFilter must be ASCII only
            try:
                url_filter.encode('ascii')
            except UnicodeEncodeError:
                continue
                
            resource_types = get_resource_types(options)
            
            rule = {
                "id": rule_id,
                "priority": 1,
                "action": {"type": "block"},
                "condition": {
                    "urlFilter": url_filter,
                    "resourceTypes": resource_types if resource_types else ALL_RESOURCES
                }
            }
            
            # Handle domain-specific rules
            domain_options = [o for o in options if o.startswith('domain=')]
            if domain_options:
                domains_str = domain_options[0].replace('domain=', '')
                domains = [d.lstrip('~') for d in domains_str.split('|') if d]
                excluded = [d.lstrip('~') for d in domains_str.split('|') if d.startswith('~')]
                if domains:
                    rule["condition"]["initiatorDomains"] = domains
                if excluded:
                    rule["condition"]["excludedInitiatorDomains"] = excluded
            
            rules.append(rule)
            rule_id += 1
            block_count += 1
            
        except Exception:
            continue
    
    print(f"  → {block_count} rules generated")
    return rules


def add_fallback_rules(rules, start_id):
    """Adaugă reguli hardcodate pentru domeniile majore de ads/tracking"""
    fallback_domains = {
        "ads": [
            "doubleclick.net", "googleadservices.com", "googlesyndication.com",
            "google-analytics.com", "googletagmanager.com", "googletagservices.com",
            "adservice.google.com", "pagead2.googlesyndication.com",
            "adnxs.com", "adsafeprotected.com", "advertising.com",
            "amazon-adsystem.com", "criteo.com", "criteo.net",
            "facebook.com/tr", "connect.facebook.net",
            "moatads.com", "openx.net", "outbrain.com",
            "pubmatic.com", "rubiconproject.com", "scorecardresearch.com",
            "sharethis.com", "taboola.com", "yieldmo.com",
            "zedo.com", "adsrvr.org", "addthis.com",
            "adzerk.net", "bluekai.com", "casalemedia.com",
            "demdex.net", "exelator.com", "krxd.net",
            "lijit.com", "mathtag.com", "media.net",
            "quantserve.com", "rlcdn.com", "serving-sys.com",
            "simpli.fi", "smartadserver.com", "adsymptotic.com",
        ],
        "trackers": [
            "bat.bing.com", "clarity.ms", "hotjar.com", 
            "mouseflow.com", "fullstory.com", "crazyegg.com",
            "optimizely.com", "mixpanel.com", "amplitude.com",
            "segment.io", "segment.com", "analytics.tiktok.com",
            "cdn.mxpnl.com", "api.mixpanel.com",
        ],
        "annoyances": [
            "cookieconsent", "cookie-law", "cookie_notice",
            "gdpr", "cookie-banner", "cookiebar",
        ]
    }
    
    for domain in fallback_domains.get("ads", []):
        if len(rules) >= 14990:
            break
        rules.append({
            "id": start_id,
            "priority": 1,
            "action": {"type": "block"},
            "condition": {
                "urlFilter": f"*://*.{domain}/*",
                "resourceTypes": ["script", "image", "xmlhttprequest", "sub_frame", "ping"]
            }
        })
        start_id += 1
    
    return rules, start_id


def main():
    output_dir = Path("rules")
    output_dir.mkdir(exist_ok=True)
    
    # Global ID offsets per category — toate ID-urile trebuie să fie unice global
    ID_OFFSETS = {"ads": 1, "trackers": 20001, "annoyances": 40001}
    
    print("=== Generating Pusu AdBlocker Rules ===\n")
    
    for category, urls in SOURCES.items():
        print(f"\n--- {category.upper()} ---")
        all_rules = []
        rule_id = ID_OFFSETS.get(category, 1)
        
        # Download from filter lists
        max_rules = {"ads": 12000, "trackers": 12000, "annoyances": 5000}.get(category, 10000)
        for url in urls:
            rules = download_filter_list(url, max_rules=max_rules)
            # Re-id rules
            for rule in rules:
                rule["id"] = rule_id
                rule_id += 1
                all_rules.append(rule)
        
        # Add fallback rules for major ad domains
        if category == "ads":
            all_rules, _ = add_fallback_rules(all_rules, rule_id)
        
        # Save to file
        output_file = output_dir / f"{category}.json"
        with open(output_file, 'w') as f:
            json.dump(all_rules, f, indent=2)
        
        print(f"  Total {category} rules: {len(all_rules)}")
        print(f"  Saved to: {output_file}")
    
    print("\n✓ Rules generation complete!")
    print(f"  Files created: {list(output_dir.glob('*.json'))}")


if __name__ == "__main__":
    main()
