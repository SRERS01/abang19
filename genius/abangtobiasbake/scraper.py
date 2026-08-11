#!/usr/bin/env python3
"""
Passive Recon Scraper (safe)

- Crawls site (respect robots.txt unless --ignore-robots)
- Fetches sitemap.xml and robots.txt
- Downloads JS assets and extracts endpoints and interesting strings
- Passive subdomain enumeration via crt.sh (certificate transparency)
- Fingerprints backend tech via headers + content
- Saves output to ./output/<target>/
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

# -------- Configuration --------
USER_AGENT = "passive-recon/1.0 (+https://example.com)"
SLEEP = 0.3
DEFAULT_MAX_PAGES = 500
JS_DOWNLOAD_LIMIT = 200  # cap number of JS files to download
CRT_SH_TIMEOUT = 15

# Fingerprint patterns (non-exhaustive)
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
        return session.get(url, timeout=timeout, allow_redirects=True)
    except requests.RequestException:
        return None

def fetch_robots(session, base_root):
    robots_url = urljoin(base_root, "/robots.txt")
    r = safe_get(session, robots_url)
    return r.text if r and r.status_code == 200 else ""

def fetch_sitemap(session, base_root):
    # try /sitemap.xml first then look for <link rel="sitemap"> or robots.txt references
    sitemap_candidates = [urljoin(base_root, "/sitemap.xml")]
    for s in sitemap_candidates:
        r = safe_get(session, s)
        if r and r.status_code == 200 and "xml" in r.headers.get("Content-Type", ""):
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
    # look at X-Powered-By or Server headers explicitly
    server = headers.get("Server", "")
    xpb = headers.get("X-Powered-By", "") or headers.get("x-powered-by", "")
    if "php" in (server + xpb).lower():
        found.add("php")
    return sorted(found)

JS_ENDPOINT_REGEX = re.compile(r"""
    (?:"|')                                      # opening quote
    (\/[A-Za-z0-9\-\_\/\.\?\=&%]+)               # path-like string starting with /
    (?:"|')                                      # closing quote
    """, re.VERBOSE)

EMAIL_REGEX = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")

IP_INTERNAL_REGEX = re.compile(r"\b(10\.\d{1,3}\.\d{1,3}\.\d{1,3}|172\.(1[6-9]|2[0-9]|3[0-1])\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3})\b")

# -------- Main passive recon --------
def passive_recon(target_url, ignore_robots=False, max_pages=DEFAULT_MAX_PAGES):
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    if not target_url.startswith("http"):
        target_url = "https://" + target_url

    parsed_root = urlparse(target_url)
    base_root = f"{parsed_root.scheme}://{parsed_root.netloc}"
    domain = parsed_root.netloc

    print(f"[+] Target: {base_root}")

    robots_text = ""
    if not ignore_robots:
        robots_text = fetch_robots(session, base_root)
        if robots_text:
            print("[+] robots.txt fetched")

    sitemap_url, sitemap_text = fetch_sitemap(session, base_root)
    if sitemap_url:
        print(f"[+] sitemap found: {sitemap_url}")

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

        # respect robots disallow lines (simple substring check) unless ignoring
        if not ignore_robots and robots_text:
            for line in robots_text.splitlines():
                if line.strip().lower().startswith("disallow:"):
                    rule = line.split(":",1)[1].strip()
                    if rule and rule in url:
                        # skip URLs matching disallow rules
                        visited.add(url)
                        break
            if url in visited:
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

        # parse HTML only when HTML
        links_found = []
        if "html" in content_type.lower():
            soup = BeautifulSoup(r.text, "lxml")

            # get links
            for a in soup.find_all("a", href=True):
                href = a["href"].strip()
                if href.startswith("#") or href.lower().startswith("javascript:") or href.lower().startswith("mailto:"):
                    continue
                full = urljoin(url, href)
                full = norm_url(full)
                links_found.append(full)
                if same_domain(domain, full) and full not in visited and full not in to_visit:
                    to_visit.append(full)

            # collect assets (script/src, link[href], img[src])
            for tag in soup.find_all(["script","link","img"], src=False):
                pass
            for tag in soup.find_all(["script","img"]):
                src = tag.get("src")
                if src:
                    full = urljoin(url, src)
                    assets.add(norm_url(full))
                    if full.lower().endswith(".js") and full not in js_files:
                        js_files.append(full)
            for tag in soup.find_all("link", href=True):
                href = tag.get("href")
                if href:
                    full = urljoin(url, href)
                    assets.add(norm_url(full))

        # Extract interesting strings from page text (emails, internal IPs)
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

    # Download and statically analyze JS files (limited)
    session.headers.update({"User-Agent": USER_AGENT})
    js_count = 0
    for js in list(js_files)[:JS_DOWNLOAD_LIMIT]:
        try:
            r = safe_get(session, js, timeout=15)
            if not r or r.status_code >= 400:
                continue
            js_text = r.text
            # extract endpoints (paths starting with /)
            for m in JS_ENDPOINT_REGEX.findall(js_text):
                # ignore common file extensions for endpoints like .png .jpg etc
                if re.search(r"\.(png|jpg|jpeg|gif|svg|css|woff|woff2|ttf|ico)$", m, re.I):
                    continue
                extracted_endpoints.add(m)
            # emails and internal ips in JS
            for m in EMAIL_REGEX.findall(js_text):
                discovered_emails.add(m)
            for ip in IP_INTERNAL_REGEX.findall(js_text):
                found_internal_ips.add(ip[0] if isinstance(ip, tuple) else ip)
            assets.add(norm_url(js))
            js_count += 1
        except Exception:
            continue

    # Passive subdomain discovery using crt.sh
    subdomains = set()
    try:
        # query crt.sh for certificate data (JSON)
        query = f"https://crt.sh/?q=%25.{tldextract.extract(domain).registered_domain}&output=json"
        r = requests.get(query, timeout=CRT_SH_TIMEOUT, headers={"User-Agent": USER_AGENT})
        if r and r.status_code == 200:
            data = r.json()
            for entry in data:
                name = entry.get("name_value") or entry.get("common_name")
                if name:
                    for line in name.splitlines():
                        line = line.strip()
                        if "*" in line:
                            line = line.replace("*.", "")
                        if line.endswith(domain) and line != domain:
                            subdomains.add(line)
    except Exception:
        pass

    # Test admin path presence lightly by doing a HEAD request (passive, no brute force)
    admin_hits = []
    for p in ADMIN_PATHS:
        test_url = urljoin(base_root + "/", p)
        try:
            h = session.head(test_url, timeout=8, allow_redirects=True)
            code = h.status_code if h is not None else None
            # mark anything with <400 as present; still passive
            if code and code < 400:
                admin_hits.append({"url": test_url, "status": code})
        except Exception:
            pass

    # Build output
    outdir = os.path.join("output", domain.replace(":", "_"))
    os.makedirs(outdir, exist_ok=True)

    # JSON output
    result = {
        "target": base_root,
        "scanned_pages": len(visited),
        "findings": findings,
        "assets": sorted(list(assets)),
        "js_files_scanned": js_count,
        "extracted_endpoints": sorted(list(extracted_endpoints)),
        "emails": sorted(list(discovered_emails)),
        "internal_ips": sorted(list(found_internal_ips)),
        "subdomains_from_crt_sh": sorted(list(subdomains)),
        "admin_hits_head": admin_hits,
    }

    with open(os.path.join(outdir, "recon.json"), "w", encoding="utf-8") as jf:
        json.dump(result, jf, indent=2)

    # CSV summary
    with open(os.path.join(outdir, "pages.csv"), "w", newline="", encoding="utf-8") as cf:
        writer = csv.writer(cf)
        writer.writerow(["url", "status", "content_type", "server", "x_powered_by", "technologies", "links_count"])
        for f in findings:
            writer.writerow([f["url"], f["status"], f["content_type"], f["server"], f["x_powered_by"], ";".join(f["technologies"]), f["links_count"]])

    # Markdown human report
    md_lines = []
    md_lines.append(f"# Passive Recon Report for {base_root}\n")
    md_lines.append(f"- Scanned pages: {len(visited)}")
    md_lines.append(f"- JS files scanned: {js_count}")
    md_lines.append(f"- Extracted endpoints (sample): {', '.join(list(extracted_endpoints)[:30])}\n")
    md_lines.append("## Subdomains (from crt.sh)")
    md_lines += [f"- {s}" for s in sorted(subdomains)[:200]]
    md_lines.append("\n## Admin-like paths responding to HEAD (<400)")
    md_lines += [f"- {a['url']} ({a['status']})" for a in admin_hits]
    md_lines.append("\n## Emails found (sample)")
    md_lines += [f"- {e}" for e in sorted(discovered_emails)[:50]]
    md_lines.append("\n## Internal IPs found")
    md_lines += [f"- {i}" for i in sorted(found_internal_ips)]

    with open(os.path.join(outdir, "report.md"), "w", encoding="utf-8") as mf:
        mf.write("\n".join(md_lines))

    print(f"\n[+] Passive recon complete. Output saved to {outdir}")
    return result

# -------- CLI --------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Passive-only recon scraper")
    parser.add_argument("--ignore-robots", action="store_true", help="Ignore robots.txt (use only with permission)")
    parser.add_argument("--max-pages", type=int, default=DEFAULT_MAX_PAGES, help="Max pages to crawl")
    args = parser.parse_args()

    target = input("Target URL (https://example.com): ").strip()
    if not target:
        print("No target provided, exiting.")
        exit(1)

    passive_recon(target, ignore_robots=args.ignore_robots, max_pages=args.max_pages)

