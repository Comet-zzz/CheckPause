"""Update checking against a small JSON manifest kept in the project repo.

The manifest only needs three fields:

    {"latest": "1.6.1", "url": "https://.../CheckPause_Setup_1.6.1.exe", "notes": "..."}

Update checks must never disturb the user: every failure path here returns
None instead of raising, so being offline simply means "no update found".
"""

import json
from dataclasses import dataclass
from urllib import request

from checkpause import APP_VERSION, GITHUB_URL

_REPO = GITHUB_URL.removeprefix("https://github.com/").strip("/")

# Every mirror is consulted and the highest version wins. jsDelivr caches
# branch URLs for many hours, so trusting whichever mirror answered first let a
# stale copy hide a new release; raw.githubusercontent is authoritative but is
# frequently unreachable from mainland China, which is why both are needed.
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


class UpdateCheckError(RuntimeError):
    """Raised in strict mode when no manifest can be fetched."""


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


def fetch_manifests(opener=None):
    """Return every manifest that answered, in mirror order."""
    fetch = opener or _default_opener
    manifests = []
    for url in MANIFEST_URLS:
        try:
            payload = json.loads(fetch(url).decode("utf-8"))
        except Exception:
            continue
        if isinstance(payload, dict):
            manifests.append(payload)
    return manifests


def _manifest_to_info(manifest, current):
    """Build an UpdateInfo, or None when this manifest has nothing to offer."""
    latest = str(manifest.get("latest") or "").strip()
    url = str(manifest.get("url") or "").strip()
    if not latest or not url or not is_newer(latest, current):
        return None
    return UpdateInfo(
        version=latest,
        url=url,
        notes=str(manifest.get("notes") or "").strip(),
    )


def check_for_update(current=APP_VERSION, opener=None, strict=False):
    """Return the newest release any mirror knows about, otherwise None.

    Failures are silent by default; strict mode raises UpdateCheckError when no
    mirror answers, which manual checks use to tell being offline apart from
    being up to date.
    """
    manifests = fetch_manifests(opener)
    if not manifests:
        if strict:
            raise UpdateCheckError("no manifest could be fetched")
        return None

    best = None
    for manifest in manifests:
        info = _manifest_to_info(manifest, current)
        if info is None:
            continue
        if best is None or is_newer(info.version, best.version):
            best = info
    return best
