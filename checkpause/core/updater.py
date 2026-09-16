"""Update checking against a small JSON manifest kept in the project repo.

The manifest only needs three fields:

    {"latest": "1.5.2", "url": "https://.../CheckPause_Setup_1.5.2.exe", "notes": "..."}

Update checks must never disturb the user: every failure path here returns
None instead of raising, so being offline simply means "no update found".
"""

import json
from dataclasses import dataclass
from urllib import request

from checkpause import APP_VERSION, GITHUB_URL

_REPO = GITHUB_URL.removeprefix("https://github.com/").strip("/")

# Tried in order; the first mirror that answers wins. jsDelivr caches the repo
# at a CDN edge that is usually reachable from mainland China, where
# raw.githubusercontent.com frequently is not.
MANIFEST_URLS = (
    f"https://cdn.jsdelivr.net/gh/{_REPO}@main/version.json",
    f"https://raw.githubusercontent.com/{_REPO}/main/version.json",
)

REQUEST_TIMEOUT = 6.0


@dataclass(frozen=True)
class UpdateInfo:
    version: str
    url: str
    notes: str = ""


def parse_version(text):
    """Turn "1.5.1" into (1, 5, 1); unparsable pieces count as 0."""
    parts = []
    for chunk in str(text).strip().split("."):
        digits = "".join(character for character in chunk if character.isdigit())
        parts.append(int(digits) if digits else 0)
    return tuple(parts) or (0,)


def is_newer(candidate, current):
    left = parse_version(candidate)
    right = parse_version(current)
    width = max(len(left), len(right))
    left += (0,) * (width - len(left))
    right += (0,) * (width - len(right))
    return left > right


def _default_opener(url):
    request_object = request.Request(
        url, headers={"User-Agent": f"CheckPause/{APP_VERSION}"}
    )
    with request.urlopen(request_object, timeout=REQUEST_TIMEOUT) as response:
        return response.read()


def fetch_manifest(opener=None):
    """Return the manifest dict, or None when every mirror failed."""
    fetch = opener or _default_opener
    for url in MANIFEST_URLS:
        try:
            payload = json.loads(fetch(url).decode("utf-8"))
        except Exception:
            continue
        if isinstance(payload, dict):
            return payload
    return None


def check_for_update(current=APP_VERSION, opener=None):
    """Return UpdateInfo when a newer release exists, otherwise None."""
    manifest = fetch_manifest(opener)
    if not manifest:
        return None

    latest = str(manifest.get("latest") or "").strip()
    url = str(manifest.get("url") or "").strip()
    if not latest or not url or not is_newer(latest, current):
        return None

    return UpdateInfo(
        version=latest,
        url=url,
        notes=str(manifest.get("notes") or "").strip(),
    )
