#!/bin/bash
# Flip every noindex draft in content/drafts/ to indexed, wiring each one into
# sitemap.xml, feed.xml and llms.txt. Run only after the bench claims in the
# current content/BRIEF-*.md have been signed off.
#
#   ./tools/publish-drafts.sh              # publish all drafts
#   ./tools/publish-drafts.sh SLUG [SLUG]  # publish only these
set -euo pipefail
cd "$(dirname "$0")/.."
slugs=("$@")
if [ ${#slugs[@]} -eq 0 ]; then
  slugs=()
  for f in content/drafts/*.txt; do
    s=$(basename "$f" .txt)
    grep -q 'content="noindex' "blog/$s/index.html" 2>/dev/null && slugs+=("$s")
  done
fi
[ ${#slugs[@]} -eq 0 ] && { echo "no drafts to publish"; exit 0; }
for s in "${slugs[@]}"; do
  python3 tools/new-post.py "content/drafts/$s.txt" --publish --no-images >/dev/null
  python3 tools/blog-check.py "$s" >/dev/null || { echo "FAILED lint: $s"; exit 1; }
  echo "published $s"
done
echo
echo "Next: commit, push, then ping the search engines:"
echo "  ./scripts/indexnow.sh $(for s in "${slugs[@]}"; do printf 'https://ringmint.com/blog/%s/ ' "$s"; done)https://ringmint.com/blog/ https://ringmint.com/feed.xml"
