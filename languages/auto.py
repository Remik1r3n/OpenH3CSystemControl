"""Automatic language selection.

Rule:
- If the system language is Chinese (any locale starting with "zh"), use Simplified Chinese strings.
- If the system language is Japanese (any locale starting with "ja"), use Japanese strings.
- Otherwise, use English strings.

This module is intentionally dependency-free and safe to import early.
"""

from __future__ import annotations

import ctypes
import locale
import os
from importlib import import_module
from typing import Any, Dict, Iterable, Optional


_MUI_LANGUAGE_NAME = 0x00000008  # Prefer BCP-47 tags like "ja-JP".


def _windows_user_preferred_ui_languages() -> list[str]:
    """Return user preferred Windows UI language tags (e.g. ['ja-JP', 'en-US']).

    This is more accurate for UI language than user locale/region settings.
    Returns an empty list if unavailable.
    """
    if os.name != "nt":
        return []

    try:
        kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
        fn = getattr(kernel32, "GetUserPreferredUILanguages", None)
        if not fn:
            return []

        num_langs = ctypes.c_ulong(0)
        buffer_len = ctypes.c_ulong(0)

        # First call: get required buffer length (in WCHARs) for MULTI_SZ.
        if not fn(_MUI_LANGUAGE_NAME, ctypes.byref(num_langs), None, ctypes.byref(buffer_len)):
            return []
        if buffer_len.value <= 0:
            return []

        buffer = ctypes.create_unicode_buffer(buffer_len.value)
        if not fn(_MUI_LANGUAGE_NAME, ctypes.byref(num_langs), buffer, ctypes.byref(buffer_len)):
            return []

        # MULTI_SZ: null-separated strings ending with double null.
        multi = ctypes.wstring_at(buffer, buffer_len.value)
        return [part for part in multi.split("\x00") if part]
    except Exception:
        return []


def _windows_user_default_locale_name() -> Optional[str]:
    """Return a BCP-47-ish *locale* name like 'zh-CN' on Windows, else None."""
    if os.name != "nt":
        return None

    # GetUserDefaultLocaleName is available on modern Windows.
    try:
        kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
        buffer_len = 85  # LOCALE_NAME_MAX_LENGTH
        buffer = ctypes.create_unicode_buffer(buffer_len)
        if kernel32.GetUserDefaultLocaleName(buffer, buffer_len):
            value = buffer.value.strip()
            return value or None
    except Exception:
        return None

    return None


def _normalize_lang_tag(tag: str) -> str:
    # Examples we may see:
    # - 'zh_CN', 'zh-CN', 'ja_JP', 'ja_JP.UTF-8'
    # - 'Japanese_Japan', 'Chinese (Simplified)_China'
    # - 'ja-JP-u-ca-japanese' (BCP-47 with extensions)
    tag = tag.strip()
    if not tag:
        return ""

    # Strip common encoding / modifier suffixes: 'ja_JP.UTF-8@foo' -> 'ja_JP'
    tag = tag.split("@", 1)[0]
    tag = tag.split(".", 1)[0]

    tag = tag.replace("_", "-").lower()

    # Some Windows APIs / envs can return descriptive names; keep a cheap heuristic.
    if tag.startswith("chinese"):
        return "zh"
    if tag.startswith("japanese"):
        return "ja"

    # Rare shorthands.
    if tag in {"jp", "jpn"}:
        return "ja"

    return tag


def _iter_system_language_candidates() -> Iterable[str]:
    # 1) Windows UI language (most reliable for this app on Windows)
    for ui_tag in _windows_user_preferred_ui_languages():
        yield ui_tag

    # 2) Windows locale/region format (can differ from UI language)
    win_locale = _windows_user_default_locale_name()
    if win_locale:
        yield win_locale

    # 3) Python locale (may be influenced by user settings / env)
    try:
        loc = locale.getlocale()[0]
        if loc:
            yield loc
    except Exception:
        pass

    try:
        default_loc = locale.getdefaultlocale()[0]  # deprecated in 3.15, still works today
        if default_loc:
            yield default_loc
    except Exception:
        pass

    # 4) Environment variables (common on non-Windows; harmless on Windows)
    for key in ("LC_ALL", "LC_MESSAGES", "LANG"):
        value = os.environ.get(key)
        if value:
            yield value


def is_system_language_chinese() -> bool:
    return get_language_module_name() == "languages.zhcn"


def is_system_language_japanese() -> bool:
    return get_language_module_name() == "languages.ja"


def get_language_module_name() -> str:
    # Select based on the *first* matching language candidate.
    # This avoids a common Windows pitfall where secondary languages (e.g. an IME)
    # would otherwise override the primary UI language.
    for raw_tag in _iter_system_language_candidates():
        tag = _normalize_lang_tag(raw_tag)
        if not tag:
            continue
        if tag.startswith("zh"):
            return "languages.zhcn"
        if tag.startswith("ja"):
            return "languages.ja"
    return "languages.en"


def apply_language(target_globals: Dict[str, Any]) -> str:
    """Load language constants and inject into target_globals.

    Returns the imported module name (e.g. 'languages.zhcn').
    """
    module_name = get_language_module_name()
    module = import_module(module_name)

    for name, value in vars(module).items():
        if name.isupper():
            target_globals[name] = value

    return module_name
