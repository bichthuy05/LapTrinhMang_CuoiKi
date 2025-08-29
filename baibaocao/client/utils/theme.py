# client/utils/theme.py
from __future__ import annotations

from typing import Callable, Dict, List


ThemePalette = Dict[str, str]


LIGHT: ThemePalette = {
    "app_bg": "#ffffff",
    "text_fg": "#000000",
    "muted_fg": "#444444",
    "bubble_self_bg": "#dbf4ff",
    "bubble_other_bg": "#f1f1f1",
    "bubble_text_fg": "#000000",
    "bubble_meta_fg": "#555555",
}


DARK: ThemePalette = {
    "app_bg": "#121212",
    "text_fg": "#e8e8e8",
    "muted_fg": "#aaaaaa",
    "bubble_self_bg": "#0d3b66",
    "bubble_other_bg": "#1e1e1e",
    "bubble_text_fg": "#e8e8e8",
    "bubble_meta_fg": "#bbbbbb",
}


_current_name: str = "light"
_listeners: List[Callable[[str], None]] = []


def get_theme_name() -> str:
    return _current_name


def get_palette() -> ThemePalette:
    return LIGHT if _current_name == "light" else DARK


def get_color(key: str, default: str | None = None) -> str:
    return get_palette().get(key, default or "#000000")


def set_theme(name: str) -> None:
    global _current_name
    if name not in ("light", "dark"):
        return
    if _current_name == name:
        return
    _current_name = name
    for cb in list(_listeners):
        try:
            cb(_current_name)
        except Exception:
            pass


def toggle_theme() -> str:
    set_theme("dark" if _current_name == "light" else "light")
    return _current_name


def add_listener(cb: Callable[[str], None]) -> None:
    if cb not in _listeners:
        _listeners.append(cb)


def remove_listener(cb: Callable[[str], None]) -> None:
    try:
        _listeners.remove(cb)
    except ValueError:
        pass


