import logging
from typing import List, Union
from pynput.keyboard import Key, KeyCode

logger = logging.getLogger("input.key")

KEY_ALIASES = {
    "ctrl": Key.ctrl,
    "ctrl_l": Key.ctrl_l,
    "ctrl_r": Key.ctrl_r,
    "maj": Key.shift,
    "shift": Key.shift,
    "shift_l": Key.shift_l,
    "shift_r": Key.shift_r,
    "alt": Key.alt,
    "alt_l": Key.alt_l,
    "alt_r": Key.alt_r,
    "alt_gr": Key.alt_gr,
    "cmd": Key.cmd,
    "cmd_r": Key.cmd_r,
    "space": Key.space,
    "tab": Key.tab,
    "enter": Key.enter,
    "retour": Key.backspace,
    "backspace": Key.backspace,
    "suppr": Key.delete,
    "delete": Key.delete,
    "esc": Key.esc,
    "echap": Key.esc,
    "haut": Key.up,
    "up": Key.up,
    "bas": Key.down,
    "down": Key.down,
    "gauche": Key.left,
    "left": Key.left,
    "droite": Key.right,
    "right": Key.right,
    "home": Key.home,
    "fin": Key.end,
    "end": Key.end,
    "page_haut": Key.page_up,
    "page_up": Key.page_up,
    "page_bas": Key.page_down,
    "page_down": Key.page_down,
    "insert": Key.insert,
    "verr_maj": Key.caps_lock,
    "caps_lock": Key.caps_lock,
    "num_lock": Key.num_lock,
    "scroll_lock": Key.scroll_lock,
    "print_screen": Key.print_screen,
    "pause": Key.pause,
    "menu": Key.menu,
    "f1": Key.f1, "f2": Key.f2, "f3": Key.f3, "f4": Key.f4,
    "f5": Key.f5, "f6": Key.f6, "f7": Key.f7, "f8": Key.f8,
    "f9": Key.f9, "f10": Key.f10, "f11": Key.f11, "f12": Key.f12,
    "f13": Key.f13, "f14": Key.f14, "f15": Key.f15, "f16": Key.f16,
    "f17": Key.f17, "f18": Key.f18, "f19": Key.f19, "f20": Key.f20,
    "f21": Key.f21, "f22": Key.f22, "f23": Key.f23, "f24": Key.f24,
    "media_next": Key.media_next,
    "media_previous": Key.media_previous,
    "media_play_pause": Key.media_play_pause,
    "media_stop": Key.media_stop,
    "media_volume_mute": Key.media_volume_mute,
    "media_volume_down": Key.media_volume_down,
    "media_volume_up": Key.media_volume_up,
}

KEY_NORMALIZE = {
    Key.ctrl_l: Key.ctrl,
    Key.ctrl_r: Key.ctrl,
    Key.shift_l: Key.shift,
    Key.shift_r: Key.shift,
    Key.alt_l: Key.alt,
    Key.alt_r: Key.alt,
}


def key_from_str(key_str: str) -> Union[KeyCode, Key]:
    """
    Convert a textual key specification to a KeyCode or Key object.

    Accepts special key names in French or English (e.g. "ctrl", "maj", "echap",
    "haut", "f1") as well as single characters (e.g. "a", "1"). Comparison is
    case-insensitive and ignores leading/trailing whitespace.

    :param key_str: Key specification (e.g. "ctrl", "maj", "a", "f1", "up").
    :return: The corresponding Key or KeyCode object.
    :raises ValueError: If the specification does not match any known key.
    """
    key_str = key_str.strip().lower()
    if key_str in KEY_ALIASES:
        return KEY_ALIASES[key_str]
    if len(key_str) == 1:
        return KeyCode.from_char(key_str)
    raise ValueError(f"Unknown key: {key_str!r}")


def combination_from_str(combination_str: str) -> List[Union[KeyCode, Key]]:
    """
    Convert a textual key combination specification to a list of KeyCode/Key.

    The string must contain keys separated by "+" (e.g. "ctrl+f1", "maj+alt+f1",
    "ctrl+c"). Each element is converted individually via :func:`key_from_str`.

    :param combination_str: Key combination separated by "+" (e.g. "ctrl+c", "maj+alt+f1").
    :return: List of Key or KeyCode objects composing the combination.
    :raises ValueError: If any element does not match a known key.
    """
    return [key_from_str(k) for k in combination_str.split("+")]


def normalize_key(key: Union[KeyCode, Key]) -> Union[KeyCode, Key]:
    """
    Normalize modifier variants to their generic form.

    Maps left/right variants (ctrl_l, ctrl_r, shift_l, shift_r, alt_l, alt_r)
    to their generic counterpart (ctrl, shift, alt) so that combinations
    involving a generic modifier accept either side.

    :param key: The key to normalize.
    :return: The normalized key.
    """
    return KEY_NORMALIZE.get(key, key)


def patch_win32_key(key: KeyCode):
    """
    Patch a win32-specific bug where KeyCode characters have incorrect offsets.

    On Windows, pynput may return characters with ASCII codes below 65 that
    are shifted by 64. This method corrects such cases by adding 64 to the
    character code and converting it back to lowercase.

    :param key: The key to patch.
    :return: The patched key, or the original key if no patch is needed.
    """
    if not "win32" in key.__class__.__module__:
        return key

    if hasattr(key, "char") and key.char:
        o = ord(key.char[0])
        if o < 65:
            return KeyCode.from_char(chr(o+64).lower())

    return key