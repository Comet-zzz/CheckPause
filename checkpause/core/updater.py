"""Update checking against a small JSON manifest kept in the project repo.

The manifest only needs three fields:

    {"latest": "1.6.1", "url": "https://.../CheckPause_Setup_1.6.1.zip", "notes": "..."}

Update checks must never disturb the user: every failure path here returns
None instead of raising, so being offline simply means "no update found".
"""

import base64
import binascii
import hashlib
import json
import platform
import re
import sys
import tempfile
import zipfile
import zlib
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from urllib import error, request
from urllib.parse import urlsplit

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from checkpause import APP_VERSION, GITHUB_URL
from checkpause.core.update_keys import UPDATE_PUBLIC_KEY
from checkpause.data.settings import DEFAULT_SERVER_URL

_REPO = GITHUB_URL.removeprefix("https://github.com/").strip("/")

# The project's own server is asked first. It is fast from mainland China and
# serves the manifest straight from disk, with no cache that can hide a
# release, so its answer is trustworthy on its own.
PRIMARY_MANIFEST_URLS = (f"{DEFAULT_SERVER_URL}/version.json",)

# The GitHub mirrors stay as fallbacks for the day the server is unreachable.
# jsDelivr caches branch URLs for many hours, so trusting whichever mirror
# answered first let a stale copy hide a new release; raw.githubusercontent is
# authoritative but is frequently unreachable from mainland China. The
# thorough check consults all three and keeps the highest version, which is
# what catches a primary copy that has gone stale.
FALLBACK_MANIFEST_URLS = (
    f"https://cdn.jsdelivr.net/gh/{_REPO}@main/version.json",
    f"https://raw.githubusercontent.com/{_REPO}/main/version.json",
)

MANIFEST_URLS = PRIMARY_MANIFEST_URLS + FALLBACK_MANIFEST_URLS

# A tiny JSON manifest never legitimately needs longer; this only bounds the
# wait for a mirror that is unreachable or black-holed.
REQUEST_TIMEOUT = 4.0
DOWNLOAD_TIMEOUT = 15.0
DOWNLOAD_CHUNK_SIZE = 64 * 1024
MAX_UPDATE_SIZE = 1024 * 1024 * 1024


def platform_key(system=None, machine=None):
    """A stable OS/architecture key used to pick the right download.

    A release manifest carries a ``urls`` map keyed by these values, so one
    version can offer a Windows installer and separate macOS disk images.
    """
    system = system or sys.platform
    machine = (machine or platform.machine()).lower()
    arm = machine in ("arm64", "aarch64")
    if system == "win32":
        return "windows-arm64" if arm else "windows-x86_64"
    if system == "darwin":
        return "macos-arm64" if arm else "macos-x86_64"
    return "linux-arm64" if arm else "linux-x86_64"


@dataclass(frozen=True)
class UpdateInfo:
    version: str
    url: str
    notes: str = ""
    sha256: str = ""


class UpdateCheckError(RuntimeError):
    """Raised in strict mode when no manifest can be fetched."""


class UpdateDownloadError(RuntimeError):
    """Raised when an update archive cannot be downloaded or verified."""


class UpdateDownloadCancelledError(RuntimeError):
    """Raised when the user cancels an update download."""


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
    request_object = request.Request(url, headers={"User-Agent": f"CheckPause/{APP_VERSION}"})
    with request.urlopen(request_object, timeout=REQUEST_TIMEOUT) as response:
        return response.read()


def _manifest_payload(manifest):
    """The exact bytes the release tool signs: the manifest without ``sig``."""
    body = {key: value for key, value in manifest.items() if key != "sig"}
    return json.dumps(
        body,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _verify_manifest(manifest):
    """Return a manifest only after its Ed25519 signature checks out.

    An empty ``UPDATE_PUBLIC_KEY`` means legacy/test mode. Production clients
    always carry a key, so a stripped or forged signature is rejected.
    """
    if not UPDATE_PUBLIC_KEY:
        return manifest
    signature = str(manifest.get("sig") or "").strip()
    if not signature:
        return None
    try:
        public_key = Ed25519PublicKey.from_public_bytes(
            base64.b64decode(UPDATE_PUBLIC_KEY, validate=True)
        )
        public_key.verify(
            base64.b64decode(signature, validate=True),
            _manifest_payload(manifest),
        )
    except (ValueError, InvalidSignature, binascii.Error):
        return None
    return manifest


def _fetch_manifest(url, fetch):
    """Return this mirror's signed manifest, or None when it cannot be used."""
    try:
        payload = json.loads(fetch(url).decode("utf-8-sig"))
    except Exception:
        return None
    if not isinstance(payload, dict):
        return None
    return _verify_manifest(payload)


def _sha256_is_valid(value):
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def fetch_manifests(opener=None, urls=MANIFEST_URLS):
    """Return every manifest that answered, in the order the URLs were given.

    Mirrors are queried at the same time: fetching them one after another made
    the user wait for each mirror's timeout in turn, so a blocked raw.github
    added its whole timeout to every check even though jsDelivr had already
    answered.
    """
    fetch = opener or _default_opener
    with ThreadPoolExecutor(max_workers=max(1, len(urls))) as pool:
        manifests = pool.map(lambda url: _fetch_manifest(url, fetch), urls)
    return [manifest for manifest in manifests if manifest is not None]


def _download_url(manifest, key):
    """This platform's download URL, or "" when the manifest has none."""
    urls = manifest.get("urls")
    if isinstance(urls, dict):
        url = str(urls.get(key) or "").strip()
        if url:
            return url
    # The single ``url`` field, and the clients that read it, point at the
    # Windows installer. Windows may fall back to it; a macOS client must not,
    # or it would download an unusable .exe.
    if key.startswith("windows"):
        return str(manifest.get("url") or "").strip()
    return ""


def _manifest_to_info(manifest, current, key):
    """Build an UpdateInfo, or None when this manifest has nothing to offer."""
    latest = str(manifest.get("latest") or "").strip()
    url = _download_url(manifest, key)
    if not latest or not url or not is_newer(latest, current):
        return None
    hashes = manifest.get("sha256")
    digest = ""
    if isinstance(hashes, dict):
        digest = str(hashes.get(key) or "").strip().lower()
    if digest and not _sha256_is_valid(digest):
        return None
    # Windows updates are downloaded and run in-app, so a signed manifest must
    # pin the archive. macOS/Linux only open the release page in a browser.
    if UPDATE_PUBLIC_KEY and key.startswith("windows") and not digest:
        return None
    return UpdateInfo(
        version=latest,
        url=url,
        notes=str(manifest.get("notes") or "").strip(),
        sha256=digest,
    )


def _best_info(manifests, current, key):
    """The newest usable update across every manifest, or None."""
    best = None
    for manifest in manifests:
        info = _manifest_to_info(manifest, current, key)
        if info is None:
            continue
        if best is None or is_newer(info.version, best.version):
            best = info
    return best


def check_for_update(current=APP_VERSION, opener=None, strict=False, quick=False, key=None):
    """Return the newest release any mirror knows about, otherwise None.

    Failures are silent by default; strict mode raises UpdateCheckError when no
    mirror answers, which manual checks use to tell being offline apart from
    being up to date.

    ``quick`` makes a manual check feel instant by trusting the project's own
    server on its own and never waiting for the GitHub fallbacks to confirm an
    "already up to date" answer. Those fallbacks are consulted only when the
    server itself is unreachable. The background check stays thorough and
    compares every mirror, which is what notices a primary copy gone stale.
    """
    manifests = fetch_manifests(opener, PRIMARY_MANIFEST_URLS if quick else MANIFEST_URLS)
    if quick and not manifests:
        manifests = fetch_manifests(opener, FALLBACK_MANIFEST_URLS)
    if not manifests:
        if strict:
            raise UpdateCheckError("no manifest could be fetched")
        return None
    return _best_info(manifests, current, key or platform_key())


def _check_download_cancelled(should_cancel):
    if should_cancel is not None and should_cancel():
        raise UpdateDownloadCancelledError()


def _is_https_url(url):
    if not isinstance(url, str):
        return False
    try:
        parsed_url = urlsplit(url)
    except ValueError:
        return False
    return parsed_url.scheme == "https" and bool(parsed_url.hostname)


def _download_archive(url, archive_part, progress, should_cancel, fetch):
    request_object = request.Request(
        url,
        headers={"User-Agent": f"CheckPause/{APP_VERSION}"},
    )
    with fetch(request_object, timeout=DOWNLOAD_TIMEOUT) as response:
        if not _is_https_url(response.geturl()):
            raise UpdateDownloadError("download redirected away from HTTPS")
        content_length = response.headers.get("Content-Length")
        total = int(content_length) if content_length else 0
        if total < 0 or total > MAX_UPDATE_SIZE:
            raise UpdateDownloadError("update archive size is invalid")

        downloaded = 0
        digest = hashlib.sha256()
        if progress is not None:
            progress(downloaded, total)
        with archive_part.open("wb") as output:
            while True:
                _check_download_cancelled(should_cancel)
                chunk = response.read(DOWNLOAD_CHUNK_SIZE)
                if not chunk:
                    break
                downloaded += len(chunk)
                if downloaded > MAX_UPDATE_SIZE:
                    raise UpdateDownloadError("update archive is too large")
                digest.update(chunk)
                output.write(chunk)
                if progress is not None:
                    progress(downloaded, total)
        if total and downloaded != total:
            raise UpdateDownloadError("download size does not match")
        return digest.hexdigest()


def _extract_installer(archive_path, installer_part, installer_name, should_cancel):
    with zipfile.ZipFile(archive_path) as archive:
        matches = [member for member in archive.infolist() if member.filename == installer_name]
        if len(matches) != 1:
            raise UpdateDownloadError("installer is missing from the update archive")
        member = matches[0]
        if member.file_size > MAX_UPDATE_SIZE:
            raise UpdateDownloadError("installer is too large")

        extracted = 0
        with archive.open(member) as source, installer_part.open("wb") as output:
            while True:
                _check_download_cancelled(should_cancel)
                chunk = source.read(DOWNLOAD_CHUNK_SIZE)
                if not chunk:
                    break
                extracted += len(chunk)
                if extracted > MAX_UPDATE_SIZE:
                    raise UpdateDownloadError("installer is too large")
                output.write(chunk)
        if extracted != member.file_size:
            raise UpdateDownloadError("installer size does not match")


def download_update(
    url,
    version,
    progress=None,
    should_cancel=None,
    download_dir=None,
    opener=None,
    expected_sha256="",
):
    """Download a Windows update archive and return its verified installer path."""
    if not isinstance(version, str) or not re.fullmatch(r"\d+(?:\.\d+)*", version):
        raise UpdateDownloadError("invalid version")
    if not _is_https_url(url):
        raise UpdateDownloadError("update URL must use HTTPS")
    expected_sha256 = str(expected_sha256 or "").strip().lower()
    if expected_sha256 and not _sha256_is_valid(expected_sha256):
        raise UpdateDownloadError("expected archive hash is invalid")

    installer_name = f"CheckPause_Setup_{version}.exe"
    update_dir = Path(download_dir or tempfile.gettempdir()) / "CheckPause" / "updates"
    archive_path = update_dir / f"{installer_name}.zip"
    archive_part = update_dir / f"{installer_name}.zip.part"
    installer_path = update_dir / installer_name
    installer_part = update_dir / f"{installer_name}.part"
    fetch = opener or request.urlopen

    _check_download_cancelled(should_cancel)
    try:
        update_dir.mkdir(parents=True, exist_ok=True)
        actual_sha256 = _download_archive(url, archive_part, progress, should_cancel, fetch)
        if expected_sha256 and actual_sha256 != expected_sha256:
            raise UpdateDownloadError("update archive hash does not match")
        archive_part.replace(archive_path)
        _extract_installer(archive_path, installer_part, installer_name, should_cancel)
        with installer_part.open("rb") as installer:
            if installer.read(2) != b"MZ":
                raise UpdateDownloadError("installer file is invalid")
        installer_part.replace(installer_path)
        return str(installer_path)
    except UpdateDownloadCancelledError:
        raise
    except UpdateDownloadError:
        raise
    except (
        OSError,
        error.URLError,
        ValueError,
        zipfile.BadZipFile,
        zipfile.LargeZipFile,
        RuntimeError,
        EOFError,
        zlib.error,
    ) as exc:
        raise UpdateDownloadError(str(exc)) from exc
    finally:
        for partial_path in (archive_part, installer_part):
            try:
                partial_path.unlink()
            except FileNotFoundError:
                pass
            except OSError as exc:
                raise UpdateDownloadError(str(exc)) from exc
