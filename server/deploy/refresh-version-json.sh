#!/usr/bin/env bash
#
# Keep /srv/downloads/version.json in step with the repository manifest.
#
# The client checks this file first: serving it from this machine keeps update
# checks fast from mainland China, and because it is read straight from disk
# there is no CDN cache that can hide a release. GitHub is still the source of
# truth, so the file is refreshed from the repository on a timer.
#
# The download is written to a temporary file and renamed into place, so a
# request either sees the previous copy or the new one, never a half-written
# file. If anything fails the existing copy is left untouched, which is what
# lets the client fall back to the GitHub mirrors.

set -euo pipefail

DEST=/srv/downloads/version.json
SOURCE="https://raw.githubusercontent.com/Comet-zzz/CheckPause/main/version.json"

tmp="$(mktemp /srv/downloads/.version.json.XXXXXX)"
trap 'rm -f "$tmp"' EXIT

if ! curl -fsS --max-time 20 -o "$tmp" "$SOURCE"; then
    echo "could not fetch $SOURCE; keeping the existing manifest" >&2
    exit 1
fi

# Refuse to publish anything the client cannot parse, such as an error page.
python3 -c 'import json,sys; json.load(open(sys.argv[1]))' "$tmp"

chmod 644 "$tmp"
mv -f "$tmp" "$DEST"
trap - EXIT
