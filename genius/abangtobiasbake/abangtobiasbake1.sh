#!/bin/bash

if [ -z "$1" ]; then
    echo "Usage: $0 <target-root-domain>"
    exit 1
fi

for cmd in whatweb jq searchsploit subfinder host; do
    if ! command -v "$cmd" &> /dev/null; then
        echo -e "\033[1;31m[-] Error:\033[0m Required tool '$cmd' is not installed."
        exit 1
    fi
done

ROOT_DOMAIN=$1
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
TMP_SUBDOMAINS="/tmp/subs_${ROOT_DOMAIN}.txt"

# Proactively wipe old report files from previous runs to prevent stale logs
rm -f report_*${ROOT_DOMAIN}.txt
rm -f "$TMP_SUBDOMAINS"

echo "=================================================="
echo "    SUBDOMAIN TAKEOVER & EXPLOIT ENGINE"
echo "    Root Scope: $ROOT_DOMAIN"
echo "=================================================="

echo -e "\n\033[1;34m[+]\033[0m Fetching subdomains via Subfinder..."
subfinder -d "$ROOT_DOMAIN" -silent -o "$TMP_SUBDOMAINS"

if [ ! -s "$TMP_SUBDOMAINS" ]; then
    echo -e "\033[1;31m[-]\033[0m No subdomains found."
    rm -f "$TMP_SUBDOMAINS"
    exit 1
fi

while read -r sub; do
    [ -z "$sub" ] && continue
    
    # Force strict space trim on subdomain name string
    sub=$(echo "$sub" | xargs)
    
    if ! host "$sub" &>/dev/null; then
        echo -e "  \033[1;30m[-] Skipping unresolvable host:\033[0m $sub"
        continue
    fi
    
    TARGET_URL=""
    if curl -s -m 4 -o /dev/null -I -w "%{http_code}" "https://$sub" 2>/dev/null | grep -qE "^[1-5]"; then
        TARGET_URL="https://$sub"
    elif curl -s -m 4 -o /dev/null -I -w "%{http_code}" "http://$sub" 2>/dev/null | grep -qE "^[1-5]"; then
        TARGET_URL="http://$sub"
    fi
    
    if [ -z "$TARGET_URL" ]; then
        continue
    fi

    echo -e "\n\033[1;35m[*] Active Asset Verified:\033[0m $TARGET_URL"

    # --- SUBDOMAIN TAKEOVER CHECKING PHASE ---
    BODY_DATA=$(curl -s -m 4 -A "$UA" -L "$TARGET_URL" | head -c 50000)

    if echo "$BODY_DATA" | grep -qi "There isn't a GitHub Pages site here"; then
        echo -e "  \033[1;41m[CRITICAL] VULNERABLE TO SUBDOMAIN TAKEOVER:\033[0m $sub (GitHub Pages)"
    elif echo "$BODY_DATA" | grep -qi "NoSuchBucket"; then
        echo -e "  \033[1;41m[CRITICAL] VULNERABLE TO SUBDOMAIN TAKEOVER:\033[0m $sub (Amazon S3)"
    elif echo "$BODY_DATA" | grep -qiE "There's nothing here, yet|no-such-app"; then
        echo -e "  \033[1;41m[CRITICAL] VULNERABLE TO SUBDOMAIN TAKEOVER:\033[0m $sub (Heroku)"
    elif echo "$BODY_DATA" | grep -qi "Help Center Closed"; then
        echo -e "  \033[1;41m[CRITICAL] VULNERABLE TO SUBDOMAIN TAKEOVER:\033[0m $sub (Zendesk)"
    fi
    # ------------------------------------------

    DOMAIN=$(echo "$TARGET_URL" | sed -e 's|^[^/]*//||' -e 's|/.*||')
    LOG_FILE="report_${DOMAIN}.txt"
    TMP_JSON="/tmp/whatweb_${DOMAIN}.json"

    # Initialize individual log files cleanly
    echo "==================================================" > "$LOG_FILE"
    echo "BUG BOUNTY EXPLOIT RECON REPORT" >> "$LOG_FILE"
    echo "Target endpoint: $TARGET_URL" >> "$LOG_FILE"
    echo "==================================================" >> "$LOG_FILE"

    whatweb --log-json="$TMP_JSON" --color=never --user-agent="$UA" "$TARGET_URL" > /dev/null 2>&1

    if [ -s "$TMP_JSON" ]; then
        jq -r '.[] | .plugins | to_entries[] | "\(.key)|\(.value.version? // "")"' "$TMP_JSON" 2>/dev/null | sort -u | while IFS="|" read -r tech_name tech_ver; do
            [ -z "$tech_name" ] && continue
            tech_name=$(echo "$tech_name" | xargs)
            tech_ver=$(echo "$tech_ver" | xargs)
            low_name=$(echo "$tech_name" | tr '[:upper:]' '[:lower:]')

            case "$low_name" in
                httpserver|http-server|country|ip|redirectlocation|cookies|html5|title|uncommonheaders|script|httponly) continue ;;
                securityheaders|strict-transport-security|x-xss-protection|x-frame-options|x-content-type-options|frame) continue ;;
                content-type|charset|request-id|set-cookie|meta-generator|passwordfield|google-analytics|open-graph-protocol) continue ;;
                content-language|meta-author|x-ua-compatible) continue ;;
                cloudflare|cf-ray|cf-cache-status|alt-svc|hsts|nosniff|secure) continue ;;
            esac

            if [ ! -z "$tech_ver" ]; then
                search_query="${tech_name} ${tech_ver}"
            else
                case "$low_name" in apache|nginx|iis|lighttpd) continue ;; esac
                search_query="${tech_name}"
            fi
            
            searchsploit "$search_query" | grep -Ei '(\.py|\.rb|\.sh|\.pl|\.php|Exploit Title|----|Shellcodes|^$)' | tee -a "$LOG_FILE"
        done
    fi
    rm -f "$TMP_JSON"
    
    # Self-Clean: If the file is just headers (empty of exploits), delete it instantly
    if [ -f "$LOG_FILE" ]; then
        file_size=$(wc -c < "$LOG_FILE")
        if [ "$file_size" -lt 300 ]; then
            rm -f "$LOG_FILE"
        fi
    fi
done < "$TMP_SUBDOMAINS"

rm -f "$TMP_SUBDOMAINS"
echo -e "\n\033[1;32m[+] Campaign Finished.\033[0m"

