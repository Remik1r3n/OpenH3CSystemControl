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


def _windows_user_default_locale_name() -> Optional[str]:
    """Return a BCP-47-ish locale name like 'zh-CN' on Windows, else None."""
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
    # Examples we may see: 'zh_CN', 'zh-CN', 'ja_JP', 'Japanese_Japan', 'Chinese (Simplified)_China'
    tag = tag.strip().replace("_", "-").lower()
    # Some Windows APIs / envs can return descriptive names; keep a cheap heuristic.
    if tag.startswith("chinese"):
        return "zh"
    if tag.startswith("japanese"):
        return "ja"
    return tag


def _iter_system_language_candidates() -> Iterable[str]:
    # 1) Windows UI locale name (most reliable for this app)
    win_tag = _windows_user_default_locale_name()
    if win_tag:
        yield win_tag

    # 2) Python locale (may be influenced by user settings / env)
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

    # 3) Environment variables (common on non-Windows; harmless on Windows)
    for key in ("LC_ALL", "LC_MESSAGES", "LANG"):
        value = os.environ.get(key)
        if value:
            yield value


def is_system_language_chinese() -> bool:
    for raw_tag in _iter_system_language_candidates():
        tag = _normalize_lang_tag(raw_tag)
        if tag.startswith("zh"):
            return True
    return False


def is_system_language_japanese() -> bool:
    for raw_tag in _iter_system_language_candidates():
        tag = _normalize_lang_tag(raw_tag)
        if tag.startswith("ja"):
            return True
    return False


def get_language_module_name() -> str:
    if is_system_language_chinese():
        return "languages.zhcn"
    if is_system_language_japanese():
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
