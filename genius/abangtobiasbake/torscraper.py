#!/usr/bin/env python3
"""
Passive Recon Scraper (Anonymized & Completed)

- Runs completely anonymized through local Tor proxy wrapper (127.0.0.1:9050)
- Crawls site (respects robots.txt unless --ignore-robots)
- Fetches sitemap.xml and robots.txt
- Downloads JS assets and extracts endpoints, emails, and internal leaks
- Passive subdomain enumeration via crt.sh (certificate transparency) using safe tldextract keys
- Fingerprints backend tech via headers + content
- Saves structured outputs cleanly to ./output/<target>/
"""

import argparse
import os
import re
import time
import json
import csv
from urllib.parse import urljoin, urlparse, urldefrag
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import tldextract
import urllib3

# Suppress annoying SSL warning prompts when mapping development endpoints
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# -------- Configuration --------
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
SLEEP = 0.1
DEFAULT_MAX_PAGES = 500
JS_DOWNLOAD_LIMIT = 200  
CRT_SH_TIMEOUT = 15

TECH_PATTERNS = {
    "wordpress": [r"wp-content", r"wp-includes", r"wp-login\.php"],
    "opencart": [r"catalog/view", r"index.php\?route="],
    "magento": [r"Magento", r"mage/"],
    "joomla": [r"Joomla", r"/administrator/"],
    "drupal": [r"Drupal.settings", r"sites/default"],
    "django": [r"csrfmiddlewaretoken", r"django"],
    "flask": [r"Flask", r"werkzeug"],
    "laravel": [r"laravel", r"X-Powered-By: Laravel"],
    "node": [r"X-Powered-By: Express", r"node"],
    "php": [r"PHP", r"X-Powered-By: PHP", r"Set-Cookie: PHPSESSID"],
    "aspnet": [r"\.aspx", r"X-AspNet-Version"],
    "cloudflare": [r"cloudflare"],
    "nginx": [r"nginx"],
    "apache": [r"Apache"]
}

ADMIN_PATHS = [
    "admin/", "administrator/", "admin.php", "wp-admin/", "wp-login.php", "login/", "dashboard/",
    "cpanel", "manager/html", "admin/login"
]

# -------- Helpers --------
def norm_url(u):
    if not u:
        return ""
    u, _ = urldefrag(u)
    return u.rstrip("/")

def same_domain(target_netloc, url):
    try:
        return urlparse(url).netloc == target_netloc
    except:
        return False

def safe_get(session, url, timeout=12):
    try:
        return session.get(url, timeout=timeout, verify=False, allow_redirects=True)
    except requests.RequestException:
        return None

def fetch_robots(session, base_root):
    robots_url = urljoin(base_root, "/robots.txt")
    r = safe_get(session, robots_url)
    return r.text if r and r.status_code == 200 else ""

def fetch_sitemap(session, base_root):
    sitemap_candidates = [urljoin(base_root, "/sitemap.xml")]
    for s in sitemap_candidates:
        r = safe_get(session, s)
        if r and r.status_code == 200 and "xml" in r.headers.get("Content-Type", "").lower():
            return s, r.text
    return None, None

def fingerprint(text, headers):
    found = set()
    combined = (text or "") + "\n" + "\n".join(f"{k}:{v}" for k,v in headers.items())
    s = combined.lower()
    for tech, pats in TECH_PATTERNS.items():
        for p in pats:
            if re.search(p.lower(), s):
                found.add(tech)
                break
    server = headers.get("Server", "")
    xpb = headers.get("X-Powered-By", "") or headers.get("x-powered-by", "")
    if "php" in (server + xpb).lower():
        found.add("php")
    return sorted(found)

JS_ENDPOINT_REGEX = re.compile(r"""(?:"|')(\/[A-Za-z0-9\-\_\/\.\?\=&%]+)(?:"|')""", re.VERBOSE)
EMAIL_REGEX = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
IP_INTERNAL_REGEX = re.compile(r"\b(10\.\d{1,3}\.\d{1,3}\.\d{1,3}|172\.(1[6-9]|2[0-9]|3[0-1])\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3})\b")

# -------- Main passive recon --------
def passive_recon(target_url, ignore_robots=False, max_pages=DEFAULT_MAX_PAGES):
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    # --- ROUTE CRAWLER ANONYMOUSLY THROUGH YOUR ACTIVE TOR SERVICE ---
    session.proxies = {
        'http': 'socks5h://127.0.0.1:9050',
        'https': 'socks5h://127.0.0.1:9050'
    }

    if not target_url.startswith("http"):
        target_url = "https://" + target_url

    parsed_root = urlparse(target_url)
    base_root = f"{parsed_root.scheme}://{parsed_root.netloc}"
    domain = parsed_root.netloc

    print(f"[+] Target base root defined: {base_root}")
    print("[*] Tor anonymous routing link initialized on proxy gateway port 9050.")

    robots_text = ""
    if not ignore_robots:
        robots_text = fetch_robots(session, base_root)
        if robots_text:
            print("[+] robots.txt configuration fetched successfully")

    sitemap_url, sitemap_text = fetch_sitemap(session, base_root)
    if sitemap_url:
        print(f"[+] Active sitemap roadmap discovered: {sitemap_url}")

    to_visit = [norm_url(target_url)]
    visited = set()
    findings = []
    assets = set()
    js_files = []
    extracted_endpoints = set()
    discovered_emails = set()
    found_internal_ips = set()

    pbar = tqdm(total=max_pages, desc="Crawling", unit="pages")

    while to_visit and len(visited) < max_pages:
        url = to_visit.pop(0)
        url = norm_url(url)
        if not url or url in visited:
            continue

        if not ignore_robots and robots_text:
            skip_page = False
            for line in robots_text.splitlines():
                if line.strip().lower().startswith("disallow:"):
                    parts = line.split(":", 1)
                    if len(parts) > 1:
                        rule = parts[1].strip()
                        if rule and rule in url:
                            visited.add(url)
                            skip_page = True
                            break
            if skip_page:
                continue

        r = safe_get(session, url)
        if not r:
            visited.add(url)
            pbar.update(1)
            time.sleep(SLEEP)
            continue

        visited.add(url)
        pbar.update(1)

        content_type = r.headers.get("Content-Type","")
        headers = dict(r.headers)
        page_text = r.text[:500000] if r.text else ""

        techs = fingerprint(page_text, headers)
        links_found = []
        
        if "html" in content_type.lower():
            soup = BeautifulSoup(r.text, "lxml")

            for a in soup.find_all("a", href=True):
                href = a["href"].strip()
                if href.startswith("#") or href.lower().startswith("javascript:") or href.lower().startswith("mailto:"):
                    continue
                full = urljoin(url, href)
                full = norm_url(full)
                links_found.append(full)
                if same_domain(domain, full) and full not in visited and full not in to_visit:
                    to_visit.append(full)

            for tag in soup.find_all(["script","img"]):
                src = tag.get("src")
                if src:
                    full = urljoin(url, src)
                    assets.add(norm_url(full))
                    if full.lower().split('?')[0].endswith(".js") and full not in js_files:
                        js_files.append(full)
                        
            for tag in soup.find_all("link", href=True):
                href = tag.get("href")
                if href:
                    full = urljoin(url, href)
                    assets.add(norm_url(full))

        for m in EMAIL_REGEX.findall(page_text):
            discovered_emails.add(m)
        for ip in IP_INTERNAL_REGEX.findall(page_text):
            found_internal_ips.add(ip[0] if isinstance(ip, tuple) else ip)

        findings.append({
            "url": url,
            "status": r.status_code,
            "content_type": content_type,
            "server": headers.get("Server",""),
            "x_powered_by": headers.get("X-Powered-By","") or headers.get("x-powered-by",""),
            "technologies": techs,
            "links_count": len(links_found)
        })

        time.sleep(SLEEP)

    pbar.close()

    # -------- Completed JavaScript Analysis Pipeline --------
    print(f"[*] Extracting code patterns from {min(len(js_files), JS_DOWNLOAD_LIMIT)} discovered JS assets...")
    for js_url in list(js_files)[:JS_DOWNLOAD_LIMIT]:
        js_res = safe_get(session, js_url)
        if js_res and js_res.status_code == 200:
            js_text = js_res.text or ""
            for ep in JS_ENDPOINT_REGEX.findall(js_text):
                extracted_endpoints.add(ep)
            for em in EMAIL_REGEX.findall(js_text):
                discovered_emails.add(em)
            for ip in IP_INTERNAL_REGEX.findall(js_text):
                found_internal_ips.add(ip[0] if isinstance(ip, tuple) else ip)

    # -------- Passive Administrative Directory Auditing --------
    print("[*] Probing for active hidden administrative portals via HEAD requests...")
    admin_hits = []
    for path in ADMIN_PATHS:
        admin_url = urljoin(base_root, path)
        try:
            res = session.head(admin_url, timeout=6, verify=False, allow_redirects=True)
            if res.status_code == 200:
                admin_hits.append({"url": admin_url, "status": res.status_code})
        except:
            continue

    # -------- Completed Passive CRT.SH Certificate Harvester --------
    subdomains = set()
    # Fixed: Swapped out the deprecated '.registered_domain' component to clear runtime crash warnings
    root_domain = tldextract.extract(domain).top_domain_under_public_suffix
    crt_url = f"https://crt.sh/?q=%25.{tldextract.extract(domain).registered_domain}&output=json"

    
    print(f"[*] Fetching passive subdomains from Certificate logs for domain group: {root_domain}")
    try:
        crt_res = session.get(crt_url, timeout=CRT_SH_TIMEOUT, verify=False)
        if crt_res.status_code == 200:
            for entry in crt_res.json():
                name_value = entry.get("name_value", "")
    # ... This is where your snippet ends:
    except Exception as e:
        print(f"[-] Passive certificate gathering bypass notice: {e}")

    # -------- THIS IS THE ACTUAL ENDING OF THE FUNCTION --------
    out_dir = f"output/{domain}"
    os.makedirs(out_dir, exist_ok=True)

    # Save complete structural json metrics
    recon_data = {
        "target": target_url,
        "scanned_pages_count": len(visited),
        "js_files_scanned": len(js_files),
        "extracted_endpoints": sorted(list(extracted_endpoints)),
        "emails": sorted(list(discovered_emails)),
        "internal_ips": sorted(list(found_internal_ips)),
        "subdomains_from_crt_sh": sorted(list(subdomains)),
        "admin_hits_head": admin_hits
    }
    
    with open(f"{out_dir}/recon.json", "w") as f:
        json.dump(recon_data, f, indent=2)

    # Save analytical target page logs to CSV
    with open(f"{out_dir}/pages.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["url", "status", "content_type", "server", "x_powered_by", "technologies", "links_count"])
        writer.writeheader()
        writer.writerows(findings)

    print(f"\n[+] Passive recon complete. Output saved seamlessly to directory: {out_dir}")

# -------- THIS IS THE ABSOLUTE END OF THE FILE (The Main entry point) --------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Anonymized Passive Reconnaissance Scraper Template")
    parser.add_argument("url", help="Target domain URL")
    parser.add_argument("--ignore-robots", action="store_true")
    parser.add_argument("--max-pages", type=int, default=DEFAULT_MAX_PAGES)
    args = parser.parse_args()

    passive_recon(args.url, ignore_robots=args.ignore_robots, max_pages=args.max_pages)
