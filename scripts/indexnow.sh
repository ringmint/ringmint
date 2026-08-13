#!/usr/bin/env bash
# Ping IndexNow so Bing (and Yandex, Naver, Seznam) recrawl straight away
# instead of waiting to discover changes on their own schedule.
#
# Usage:
#   ./scripts/indexnow.sh                 # submit every URL in sitemap.xml
#   ./scripts/indexnow.sh https://ringmint.com/faq/ ...   # submit specific URLs
#
# Run it after pushing — IndexNow fetches the URLs, so telling it about a
# change that is not live yet just gets the old page recrawled.

set -euo pipefail

HOST="ringmint.com"
KEY="12715d644c1e4c43b9282c001e428732"
KEY_LOCATION="https://${HOST}/${KEY}.txt"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [ "$#" -gt 0 ]; then
  urls=("$@")
else
  # Pull <loc> values straight from the sitemap so the two never drift apart.
  urls=()
  while IFS= read -r line; do urls+=("$line"); done < <(
    grep -o '<loc>[^<]*</loc>' "${ROOT}/sitemap.xml" | sed -e 's|<loc>||' -e 's|</loc>||'
  )
fi

if [ "${#urls[@]}" -eq 0 ]; then
  echo "No URLs found. Is sitemap.xml missing or empty?" >&2
  exit 1
fi

# The key file must be publicly readable or IndexNow rejects the whole batch.
key_status="$(curl -s -o /dev/null -w '%{http_code}' "$KEY_LOCATION")"
if [ "$key_status" != "200" ]; then
  echo "Key file at ${KEY_LOCATION} returned HTTP ${key_status}, expected 200." >&2
  echo "Push it to the site root before submitting." >&2
  exit 1
fi

url_json="$(printf '%s\n' "${urls[@]}" | sed 's/.*/"&"/' | paste -sd, -)"
payload="{\"host\":\"${HOST}\",\"key\":\"${KEY}\",\"keyLocation\":\"${KEY_LOCATION}\",\"urlList\":[${url_json}]}"

echo "Submitting ${#urls[@]} URL(s) to IndexNow:"
printf '  %s\n' "${urls[@]}"

status="$(curl -s -o /tmp/indexnow_body.txt -w '%{http_code}' \
  -X POST "https://api.indexnow.org/indexnow" \
  -H "Content-Type: application/json; charset=utf-8" \
  -d "$payload")"

case "$status" in
  200|202) echo "OK (HTTP ${status}) — accepted." ;;
  400) echo "HTTP 400 — malformed request." >&2; cat /tmp/indexnow_body.txt >&2; exit 1 ;;
  403) echo "HTTP 403 — key not valid for this host. Check ${KEY_LOCATION}." >&2; exit 1 ;;
  422) echo "HTTP 422 — URLs do not match the host, or the key does not match." >&2; exit 1 ;;
  429) echo "HTTP 429 — too many requests. Wait and retry." >&2; exit 1 ;;
  *)   echo "Unexpected HTTP ${status}." >&2; cat /tmp/indexnow_body.txt >&2; exit 1 ;;
esac
