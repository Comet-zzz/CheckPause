"""Small secret store for the account token and the user's BYOK key.

Windows uses DPAPI (the same user can decrypt it, other users and copied files
cannot). macOS uses the login Keychain through the built-in ``security`` tool.
Linux uses libsecret's ``secret-tool`` when present. If none of those work, a
0600 file is used as a last resort so saving a key never silently fails; that
fallback is not encrypted and is documented as such.

This is not a defense against malware running as the user, only against casual
file copying and a plaintext settings.json.
"""

import base64
import contextlib
import ctypes
import json
import os
import shutil
import subprocess
import sys
import tempfile
from ctypes import wintypes

from checkpause.data.paths import DATA_DIR, SECRETS_FILE

_SERVICE = "CheckPause"
_ACCOUNT = "secrets"
_CRYPTPROTECT_UI_FORBIDDEN = 0x01
_CACHE = None
_CACHE_PATH = None


class _DataBlob(ctypes.Structure):
    _fields_ = [
        ("cbData", wintypes.DWORD),
        ("pbData", ctypes.POINTER(ctypes.c_char)),
    ]


def _blob(data):
    buffer = ctypes.create_string_buffer(data, len(data))
    return _DataBlob(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_char))), buffer


def _dpapi_call(function, data):
    if not data:
        return b""
    kernel32 = ctypes.windll.kernel32
    function.argtypes = [
        ctypes.POINTER(_DataBlob),
        ctypes.c_void_p,
        ctypes.POINTER(_DataBlob),
        ctypes.c_void_p,
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.POINTER(_DataBlob),
    ]
    function.restype = wintypes.BOOL
    kernel32.LocalFree.argtypes = [ctypes.c_void_p]
    kernel32.LocalFree.restype = ctypes.c_void_p
    input_blob, keep = _blob(data)
    output_blob = _DataBlob()
    if not function(
        ctypes.byref(input_blob),
        None,
        None,
        None,
        None,
        _CRYPTPROTECT_UI_FORBIDDEN,
        ctypes.byref(output_blob),
    ):
        raise OSError("DPAPI call failed")
    try:
        return ctypes.string_at(output_blob.pbData, output_blob.cbData)
    finally:
        kernel32.LocalFree(ctypes.cast(output_blob.pbData, ctypes.c_void_p))


def _dpapi_protect(data):
    return _dpapi_call(ctypes.windll.crypt32.CryptProtectData, data)


def _dpapi_unprotect(data):
    return _dpapi_call(ctypes.windll.crypt32.CryptUnprotectData, data)


def _read_file():
    try:
        with open(SECRETS_FILE, "rb") as handle:
            return handle.read()
    except OSError:
        return b""


def _write_file(data):
    target_dir = os.path.dirname(SECRETS_FILE) or DATA_DIR
    os.makedirs(target_dir, exist_ok=True)
    handle, temp_path = tempfile.mkstemp(prefix="secrets.", dir=target_dir)
    try:
        with os.fdopen(handle, "wb") as output:
            output.write(data)
        if os.name != "nt":
            os.chmod(temp_path, 0o600)
        os.replace(temp_path, SECRETS_FILE)
    finally:
        try:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        except OSError:
            # Best-effort cleanup; the replace already succeeded or failed.
            pass


def _remove_file():
    try:
        os.unlink(SECRETS_FILE)
    except FileNotFoundError:
        pass
    except OSError:
        # Another process or a permission issue; the caller cannot do better.
        pass


def _decode_payload(payload):
    if not payload:
        return {}
    try:
        data = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _encode_payload(secrets):
    return json.dumps(secrets, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def _keychain_get():
    try:
        result = subprocess.run(
            [_security(), "find-generic-password", "-s", _SERVICE, "-a", _ACCOUNT, "-w"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return b""
    if result.returncode != 0:
        return b""
    try:
        return base64.b64decode(result.stdout.strip(), validate=True)
    except (ValueError, TypeError):
        return b""


def _keychain_set(payload):
    value = base64.b64encode(payload).decode("ascii")
    try:
        result = subprocess.run(
            [
                _security(),
                "add-generic-password",
                "-s",
                _SERVICE,
                "-a",
                _ACCOUNT,
                "-w",
                value,
                "-U",
            ],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return result.returncode == 0


def _keychain_clear():
    with contextlib.suppress(OSError, subprocess.SubprocessError):
        subprocess.run(
            [_security(), "delete-generic-password", "-s", _SERVICE, "-a", _ACCOUNT],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )


def _security():
    return shutil.which("security") or "/usr/bin/security"


def _secret_tool_available():
    return shutil.which("secret-tool") is not None


def _secret_tool_get():
    tool = shutil.which("secret-tool")
    if not tool:
        return b""
    try:
        result = subprocess.run(
            [tool, "lookup", "service", _SERVICE, "account", _ACCOUNT],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return b""
    if result.returncode != 0:
        return b""
    try:
        return base64.b64decode(result.stdout.strip(), validate=True)
    except (ValueError, TypeError):
        return b""


def _secret_tool_set(payload):
    tool = shutil.which("secret-tool")
    if not tool:
        return False
    try:
        result = subprocess.run(
            [
                tool,
                "store",
                "--label=" + _SERVICE,
                "service",
                _SERVICE,
                "account",
                _ACCOUNT,
            ],
            input=base64.b64encode(payload).decode("ascii"),
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return result.returncode == 0


def _secret_tool_clear():
    tool = shutil.which("secret-tool")
    if not tool:
        return
    with contextlib.suppress(OSError, subprocess.SubprocessError):
        subprocess.run(
            [tool, "clear", "service", _SERVICE, "account", _ACCOUNT],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )


def _load_native():
    if sys.platform == "win32":
        raw = _read_file()
        if not raw:
            return {}
        try:
            return _decode_payload(_dpapi_unprotect(raw))
        except OSError:
            return _decode_payload(raw)
    if sys.platform == "darwin":
        return _decode_payload(_keychain_get())
    if _secret_tool_available():
        return _decode_payload(_secret_tool_get())
    return {}


def _remember(secrets):
    global _CACHE, _CACHE_PATH
    _CACHE = dict(secrets)
    _CACHE_PATH = SECRETS_FILE


def load_secrets():
    global _CACHE, _CACHE_PATH
    if _CACHE is not None and _CACHE_PATH == SECRETS_FILE:
        return dict(_CACHE)
    secrets = _load_native()
    if not secrets:
        # A native backend may be unavailable (or this may be a fresh install
        # created before the backend worked); the 0600 file is the fallback.
        secrets = _decode_payload(_read_file())
    _CACHE = dict(secrets)
    _CACHE_PATH = SECRETS_FILE
    return dict(secrets)


def save_secrets(secrets):
    global _CACHE, _CACHE_PATH
    secrets = dict(secrets)
    payload = _encode_payload(secrets)
    if sys.platform == "win32":
        try:
            _write_file(_dpapi_protect(payload))
            _remember(secrets)
            return True
        except OSError:
            pass
    elif sys.platform == "darwin":
        if _keychain_set(payload):
            _remove_file()
            _remember(secrets)
            return True
    elif _secret_tool_available() and _secret_tool_set(payload):
        _remove_file()
        _remember(secrets)
        return True
    try:
        _write_file(payload)
        _remember(secrets)
        return True
    except OSError:
        return False


def clear_secrets():
    global _CACHE, _CACHE_PATH
    _CACHE = {}
    _CACHE_PATH = SECRETS_FILE
    if sys.platform == "win32":
        _remove_file()
    elif sys.platform == "darwin":
        _keychain_clear()
        _remove_file()
    else:
        if _secret_tool_available():
            _secret_tool_clear()
        _remove_file()
